# utils.py

import uuid
import threading
from reports import process_report
from config import Config
import os
import logging
from models import db, Report

logger = logging.getLogger(__name__)


def validate_github_url(url: str) -> bool:
    return url is not None and url.startswith("https://github.com/") and len(url.split("/")) >= 5

def create_new_report(data: dict, user_id: str) -> dict:
    report_id = str(uuid.uuid4())
    report_dir_path = os.path.join(Config.REPORT_DIR, report_id)

    try:
        os.makedirs(report_dir_path, exist_ok=True)
        logger.info(f"Created directory for report {report_id}: {report_dir_path}")
        
        user_id_int = int(user_id)
        
        new_db_report = Report(
            id=report_id,
            github_url=data['githubUrl'],
            email=data['email'],
            date_range=f"{data['startDate']} - {data['endDate']}",
            status='processing',
            user_id=user_id_int,
            report_dir_path=report_dir_path
        )

        db.session.add(new_db_report)
        db.session.commit()
        logger.info(f"Report {report_id} added to database for user {user_id_int}")

        logger.info(f"Starting report processing thread for report {report_id} (user {user_id_int})")
        thread = threading.Thread(
            target=process_report,
            args=(report_id, new_db_report.github_url, new_db_report.date_range, new_db_report.email, user_id_int)
        )
        thread.start()

        return {
            'id': new_db_report.id,
            'githubUrl': new_db_report.github_url,
            'email': new_db_report.email,
            'dateRange': new_db_report.date_range,
            'status': new_db_report.status,
            'createdAt': new_db_report.created_at.isoformat()
        }

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating report entry for user {user_id}: {e}", exc_info=True)
        raise

def get_user_reports(user_id: str) -> list:
    try:
        user_id_int = int(user_id)
        user_reports_db = Report.query.filter_by(user_id=user_id_int)\
                                      .order_by(Report.created_at.desc())\
                                      .all()

        reports_list = [
            {
                'id': r.id,
                'githubUrl': r.github_url,
                'email': r.email,
                'dateRange': r.date_range,
                'status': r.status,
                'createdAt': r.created_at.isoformat()
            } for r in user_reports_db
        ]
        return reports_list

    except Exception as e:
        logger.error(f"Error fetching reports for user {user_id}: {e}", exc_info=True)
        return []