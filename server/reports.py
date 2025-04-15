import os
import json
from datetime import datetime, timezone
from github_api import get_github_files
import logging
from models import db, Report

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
             raise ValueError("Could not determine report file path.")

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        logger.info(f"Отчет сохранен: {json_path}")
        return json_path
    except Exception as e:
        logger.error(f"Ошибка генерации JSON отчета {report_id}: {str(e)}", exc_info=True)
        raise


def process_report(report_id: str, github_url: str, date_range: str, email: str, user_id: int):
    from app import app
    with app.app_context():
        report_to_update = Report.query.get(report_id)

        if not report_to_update:
            logger.error(f"Report {report_id} not found in database for processing. Aborting.")
            return

        if report_to_update.user_id != user_id:
             logger.error(f"User ID mismatch for report {report_id}. Expected {report_to_update.user_id}, got {user_id}. Aborting.")
             return

        final_status = 'failed'
        try:
            logger.info(f"Processing report {report_id} for user {user_id} - URL: {github_url}, Range: {date_range}, Email: {email}")
            start_date_str, end_date_str = date_range.split(' - ')

            files_data = get_github_files(github_url, start_date_str, end_date_str, email)

            if files_data is None:
                 logger.error(f"Failed to retrieve file data from GitHub for report {report_id}.")
            else:
                generate_json_report(report_id, files_data, report_to_update.report_dir_path)
                final_status = 'completed'
                logger.info(f"Report {report_id} processed successfully.")

        except Exception as e:
            logger.error(f"Ошибка обработки отчета {report_id} для пользователя {user_id}: {str(e)}", exc_info=True)

        finally:
            try:
                if report_to_update in db.session:
                    report_to_update.status = final_status
                    db.session.commit()
                    logger.info(f"Final status '{final_status}' saved to database for report {report_id} (user {user_id})")
                else:
                     logger.warning(f"Report {report_id} detached from session. Re-attaching to update status.")
                     report_fresh = Report.query.get(report_id)
                     if report_fresh:
                         report_fresh.status = final_status
                         db.session.commit()
                         logger.info(f"Final status '{final_status}' saved to database for report {report_id} (user {user_id}) after re-attach.")
                     else:
                          logger.error(f"Report {report_id} not found even after re-querying. Cannot update status.")

            except Exception as db_err:
                db.session.rollback()
                logger.error(f"Failed to update database status for report {report_id} to '{final_status}': {db_err}", exc_info=True)