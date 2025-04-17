# routes.py

from flask import jsonify, request, send_file, abort
from datetime import datetime
from utils import validate_github_url, create_new_report, get_user_reports
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging
import os
from models import Report
from config import Config

logger = logging.getLogger(__name__)

def register_routes(app):

    @app.route('/api/generate-report', methods=['POST'])
    @jwt_required()
    def generate_report():
        current_user_id = get_jwt_identity()
        try:
            data = request.json
            github_url = data.get('githubUrl')
            email = data.get('email')
            start_date = data.get('startDate')
            end_date = data.get('endDate')

            if not validate_github_url(github_url) or not email or not start_date or not end_date:
                 logger.warning(f"Invalid data received for generate-report from user {current_user_id}")
                 return jsonify({"error": "Некорректные данные репозитория, email или дат"}), 400

            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                if end_dt < start_dt:
                     return jsonify({"error": "Дата окончания не может быть раньше даты начала"}), 400
            except ValueError:
                logger.warning(f"Invalid date format received for generate-report from user {current_user_id}")
                return jsonify({"error": "Некорректный формат даты (YYYY-MM-DD)"}), 400

            new_report_data = create_new_report(data, current_user_id)
            logger.info(f"Report creation initiated: {new_report_data.get('id')} by user {current_user_id}")
            return jsonify(new_report_data), 201

        except Exception as e:
            logger.error(f"Ошибка в generate_report для пользователя {current_user_id}: {str(e)}", exc_info=True)
            return jsonify({"error": "Внутренняя ошибка сервера при создании отчета"}), 500


    @app.route('/api/reports', methods=['GET'])
    @jwt_required()
    def get_reports():
        current_user_id = get_jwt_identity()
        try:
            user_reports_list = get_user_reports(current_user_id)
            return jsonify(user_reports_list)
        except Exception as e:
            logger.error(f"Ошибка в get_reports для пользователя {current_user_id}: {str(e)}", exc_info=True)
            return jsonify({"error": "Внутренняя ошибка сервера при получении отчетов"}), 500


    @app.route('/api/reports/<string:report_id>/download', methods=['GET'])
    @jwt_required()
    def download_report(report_id):
        current_user_id = get_jwt_identity()
        try:
            user_id_int = int(current_user_id)
            report = Report.query.filter_by(id=report_id, user_id=user_id_int).first()

            if not report:
                logger.warning(f"Download attempt failed: Report {report_id} not found for user {user_id_int}.")
                abort(404, description="Отчет не найден или у вас нет доступа.")

            if report.status != 'completed' or not report.pdf_report_path:
                logger.warning(f"Download attempt failed: Report {report_id} is not completed or PDF path missing. Status: {report.status}, LLM Status: {report.llm_status}")
                # Slightly more specific message depending on llm_status
                if report.status == 'failed' or report.llm_status == 'failed':
                    abort(400, description="Произошла ошибка при создании отчета. Скачивание невозможно.")
                elif report.llm_status == 'skipped' and not report.pdf_report_path: # Empty report case might miss path
                     abort(400, description="Отчет не содержит файлов для анализа, PDF не сгенерирован.")
                else:
                    abort(400, description="Отчет еще не готов для скачивания.")


            pdf_path = report.get_pdf_report_file_path()

            if not pdf_path or not os.path.exists(pdf_path):
                 logger.error(f"Download failed: PDF file path invalid or file missing for report {report_id}. Path: {pdf_path}")
                 abort(500, description="Файл отчета не найден на сервере.")

            repo_name_part = report.github_url.split('/')[-1] if report.github_url else 'report'
            filename = f"CodeAnalysis_{repo_name_part}_{report_id[:8]}.pdf"

            logger.info(f"User {user_id_int} downloading report {report_id} from {pdf_path} as {filename}")
            return send_file(
                pdf_path,
                as_attachment=True,
                download_name=filename,
                mimetype='application/pdf'
            )

        except Exception as e:
            logger.error(f"Ошибка скачивания отчета {report_id} для пользователя {current_user_id}: {str(e)}", exc_info=True)
            abort(500, description="Внутренняя ошибка сервера при скачивании отчета.")