from flask import jsonify, request
from datetime import datetime
from config import Config
from utils import validate_github_url, create_new_report
import logging

logger = logging.getLogger(__name__)

def register_routes(app):
    @app.route('/api/generate-report', methods=['POST'])
    def generate_report():
        try:
            data = request.json
            github_url = data.get('githubUrl')
            email = data.get('email')
            start_date = data.get('startDate')
            end_date = data.get('endDate')
            
            if not validate_github_url(github_url) or not email:
                return jsonify({"error": "Некорректные данные"}), 400
                
            try:
                datetime.strptime(start_date, "%Y-%m-%d")
                datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError:
                return jsonify({"error": "Некорректный формат даты"}), 400

            new_report = create_new_report(data)
            
            return jsonify({
                "message": "Отчет добавлен в очередь",
                "reportId": new_report['id']
            })
            
        except Exception as e:
            logger.error(f"Ошибка в generate_report: {str(e)}", exc_info=True)
            return jsonify({"error": "Внутренняя ошибка сервера"}), 500

    @app.route('/api/reports', methods=['GET'])
    def get_reports():
        try:
            from utils import reports  # Импорт внутри функции для избежания циклических зависимостей
            return jsonify(reports)
        except Exception as e:
            logger.error(f"Ошибка в get_reports: {str(e)}", exc_info=True)
            return jsonify({"error": "Внутренняя ошибка сервера"}), 500