from models import db, Report

def clear_reports():
    db.session.query(Report).delete()
    db.session.commit()