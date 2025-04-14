import os
import json
from datetime import datetime, timezone
from config import Config
from github_api import get_github_files
import logging

logger = logging.getLogger(__name__)

def generate_json_report(report_id: str, files_data: list):
    try:
        report_dir = os.path.join(Config.REPORT_DIR, report_id)
        os.makedirs(report_dir, exist_ok=True)
        
        report_data = {
            "report_id": report_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "files": files_data
        }
        
        json_path = os.path.join(report_dir, f"report_{report_id}.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Отчет сохранен: {json_path}")
            
    except Exception as e:
        logger.error(f"Ошибка генерации отчета: {str(e)}")
        raise

def process_report(report_id: str, github_url: str, date_range: str, email: str):
    try:
        start_date, end_date = date_range.split(' - ')
        files_data = get_github_files(github_url, start_date, end_date, email)
        generate_json_report(report_id, files_data)
        
        from utils import reports
        for r in reports:
            if r['id'] == report_id:
                r['status'] = 'completed'
                
    except Exception as e:
        logger.error(f"Ошибка обработки отчета {report_id}: {str(e)}", exc_info=True)