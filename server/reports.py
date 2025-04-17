# reports.py

import os
import json
from datetime import datetime, timezone
from github_api import get_github_files
import logging
from models import db, Report
from config import Config
from llm_processor import CodeAnalyzer, PDFGenerator

logger = logging.getLogger(__name__)


def generate_json_report(report_id: str, files_data: list, report_dir_path: str):
    try:
        os.makedirs(report_dir_path, exist_ok=True)
        report_data = {
            "report_id": report_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "files": files_data
        }
        json_path = os.path.join(report_dir_path, f"report_{report_id}.json")

        if not json_path:
             raise ValueError("Could not determine JSON report file path.")

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        logger.info(f"JSON отчет сохранен: {json_path}")
        return json_path
    except Exception as e:
        logger.error(f"Ошибка генерации JSON отчета {report_id}: {str(e)}", exc_info=True)
        raise


def process_report(report_id: str, github_url: str, date_range: str, email: str, user_id: int):
    from app import app
    with app.app_context():
        json_report_path = None
        pdf_report_path = None
        final_status = 'failed'
        llm_final_status = 'failed'

        report_to_update = Report.query.get(report_id)

        if not report_to_update:
            logger.error(f"Report {report_id} not found in database for processing. Aborting.")
            return

        if report_to_update.user_id != user_id:
             logger.error(f"User ID mismatch for report {report_id}. Expected {report_to_update.user_id}, got {user_id}. Aborting.")
             report_to_update.status = 'failed'
             report_to_update.llm_status = 'skipped'
             db.session.commit()
             return

        try:
            logger.info(f"Processing report {report_id} for user {user_id} - URL: {github_url}, Range: {date_range}, Email: {email}")
            start_date_str, end_date_str = date_range.split(' - ')

            logger.info(f"[{report_id}] Fetching GitHub files...")
            files_data = get_github_files(github_url, start_date_str, end_date_str, email)

            if files_data is None:
                 logger.error(f"[{report_id}] Failed to retrieve file data from GitHub.")
                 raise RuntimeError("GitHub data retrieval failed")

            if not files_data:
                 logger.warning(f"[{report_id}] No files found on GitHub for the specified criteria.")

            logger.info(f"[{report_id}] Generating JSON report...")
            if not report_to_update.report_dir_path or not os.path.exists(report_to_update.report_dir_path):
                 logger.error(f"[{report_id}] Report directory path is missing or invalid: {report_to_update.report_dir_path}")
                 raise RuntimeError("Report directory invalid")

            json_report_path = generate_json_report(report_id, files_data, report_to_update.report_dir_path)
            logger.info(f"[{report_id}] JSON report generated at: {json_report_path}")

            if not files_data:
                 logger.info(f"[{report_id}] No files to analyze with LLM. Marking report as completed (empty).")
                 final_status = 'completed'
                 llm_final_status = 'skipped'
                 empty_pdf_path = os.path.join(Config.LLM_REPORT_DIR, report_id, f"analysis_{report_id}_empty.pdf")
                 os.makedirs(os.path.dirname(empty_pdf_path), exist_ok=True)
                 try:
                     PDFGenerator.save_to_pdf(empty_pdf_path, f"Анализ кодовой базы (Файлы не найдены)", "Не найдено коммитов или файлов для анализа по заданным критериям.")
                     pdf_report_path = empty_pdf_path
                 except Exception as pdf_err:
                     logger.error(f"[{report_id}] Не удалось создать пустой PDF отчет: {pdf_err}")
                 # Use return to jump to finally
                 return

            logger.info(f"[{report_id}] Initializing LLM Analyzer...")
            try:
                if not Config.YANDEX_FOLDER_ID or not Config.YANDEX_AUTH_TOKEN:
                     raise ValueError("Yandex credentials not configured in environment/config.")
                analyzer = CodeAnalyzer(
                    folder_id=Config.YANDEX_FOLDER_ID,
                    auth_token=Config.YANDEX_AUTH_TOKEN
                )
            except Exception as init_err:
                 logger.error(f"[{report_id}] Failed to initialize CodeAnalyzer: {init_err}", exc_info=True)
                 llm_final_status = 'failed'
                 raise

            # Check if report_to_update is still in session before committing
            if report_to_update in db.session:
                report_to_update.llm_status = 'processing'
                db.session.commit()
            else:
                # If detached, re-fetch and update
                report_fresh_intermediate = Report.query.get(report_id)
                if report_fresh_intermediate:
                    report_fresh_intermediate.llm_status = 'processing'
                    db.session.commit()
                    report_to_update = report_fresh_intermediate # Update local variable too
                else:
                    logger.error(f"[{report_id}] Failed to update llm_status to processing: Report not found.")
                    # Consider how to proceed, maybe raise error

            logger.info(f"[{report_id}] Starting LLM analysis and PDF generation...")

            llm_report_dir = os.path.join(Config.LLM_REPORT_DIR, report_id)
            os.makedirs(llm_report_dir, exist_ok=True)
            target_pdf_path = os.path.join(llm_report_dir, f"analysis_{report_id}.pdf")

            try:
                generated_pdf_path = analyzer.process_json_and_generate_pdf(
                    input_json_path=json_report_path,
                    output_pdf_path=target_pdf_path
                )
                pdf_report_path = generated_pdf_path
                llm_final_status = 'completed'
                final_status = 'completed'
                logger.info(f"[{report_id}] LLM analysis and PDF generation successful: {pdf_report_path}")

            except Exception as llm_err:
                 logger.error(f"[{report_id}] Error during LLM processing or PDF generation: {llm_err}", exc_info=True)
                 llm_final_status = 'failed'
                 final_status = 'failed'

        except Exception as e:
            logger.error(f"[{report_id}] General error in processing report: {str(e)}", exc_info=True)
            final_status = 'failed'
            if report_to_update and report_to_update.llm_status == 'pending':
                 llm_final_status = 'skipped'
            else:
                 llm_final_status = 'failed'

        finally:
            try:
                report_fresh = Report.query.get(report_id)
                if report_fresh:
                    logger.info(f"[{report_id}] Updating final status in DB: Status='{final_status}', LLM_Status='{llm_final_status}', PDF_Path='{pdf_report_path}'")
                    report_fresh.status = final_status
                    report_fresh.llm_status = llm_final_status
                    if (llm_final_status == 'completed' or llm_final_status == 'skipped') and pdf_report_path:
                         report_fresh.pdf_report_path = pdf_report_path
                    else:
                         report_fresh.pdf_report_path = None

                    db.session.commit()
                    logger.info(f"[{report_id}] Final status saved to database.")
                else:
                     logger.error(f"[{report_id}] CRITICAL: Report not found in DB during final update. Status may be incorrect.")

            except Exception as db_err:
                db.session.rollback()
                logger.error(f"[{report_id}] CRITICAL: Failed to update database status to '{final_status}' (LLM: '{llm_final_status}'): {db_err}", exc_info=True)