from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime, timezone
import os

db = SQLAlchemy()
bcrypt = Bcrypt()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    reports = db.relationship('Report', backref='author', lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


class Report(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    github_url = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    date_range = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='processing')
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    report_dir_path = db.Column(db.String(300), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def get_report_file_path(self):
        if not self.report_dir_path:
            return None
        return os.path.join(self.report_dir_path, f"report_{self.id}.json")

    def __repr__(self):
        return f'<Report {self.id} for User {self.user_id}>'