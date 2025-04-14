import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
    REPORT_DIR = os.path.abspath("reports")
    ALLOWED_EXTENSIONS = {
        '.py', '.js', '.ts', '.tsx', '.html', '.css', 
        '.java', '.cpp', '.c', '.cs', '.go', '.php', 
        '.rb', '.swift', '.kt', '.scala'
    }
    CORS_ORIGINS = ["http://localhost:3000"]
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'