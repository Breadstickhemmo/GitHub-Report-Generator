import uuid
import threading
from datetime import datetime, timezone
from reports import process_report
import logging

logger = logging.getLogger(__name__)

# Глобальный список отчетов
reports = []

def validate_github_url(url: str) -> bool:
    return url.startswith("https://github.com/") and len(url.split("/")) >= 5

def create_new_report(data: dict) -> dict:
    report_id = str(uuid.uuid4())
    new_report = {
        'id': report_id,
        'githubUrl': data['githubUrl'],
        'email': data['email'],
        'dateRange': f"{data['startDate']} - {data['endDate']}",
        'status': 'processing',
        'createdAt': datetime.now(timezone.utc).isoformat()
    }
    reports.append(new_report)
    
    thread = threading.Thread(
        target=process_report,
        args=(report_id, new_report['githubUrl'], new_report['dateRange'], new_report['email'])
    )
    thread.start()
    
    return new_report