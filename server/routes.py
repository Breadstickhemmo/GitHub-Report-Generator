from flask import jsonify, request
from datetime import datetime
from utils import validate_github_url, create_new_report, get_user_reports
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging

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
                 return jsonify({"error": "Некорректные данные репозитория, email или дат"}), 400

            try:
                datetime.strptime(start_date, "%Y-%m-%d")
                datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError:
                return jsonify({"error": "Некорректный формат даты (YYYY-MM-DD)"}), 400

            new_report_data = create_new_report(data, current_user_id)

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