import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
    REPORT_DIR = os.path.abspath("reports")
    LLM_REPORT_DIR = os.path.abspath("llm_reports")
    ALLOWED_EXTENSIONS = {
        '.py', '.js', '.ts', '.tsx', '.html', '.css',
        '.java', '.cpp', '.c', '.cs', '.go', '.php',
        '.rb', '.swift', '.kt', '.scala'
    }
    CORS_ORIGINS = ["http://localhost:3000"]
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY')

    YANDEX_FOLDER_ID = os.getenv('YANDEX_FOLDER_ID')
    YANDEX_AUTH_TOKEN = os.getenv('YANDEX_AUTH_TOKEN')