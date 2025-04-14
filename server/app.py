import os
import uuid
import base64
import time
import json
import requests
import logging
from dotenv import load_dotenv
from flask_cors import CORS
from threading import Thread
from datetime import datetime, timezone
from flask import Flask, request, jsonify

# Загрузка переменных окружения
load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
if not GITHUB_TOKEN:
    logging.error("GITHUB_TOKEN не найден в .env файле")
    exit("Ошибка: GITHUB_TOKEN не установлен")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

if not os.path.exists("reports"):
    os.makedirs("reports")

reports = []
ALLOWED_EXTENSIONS = {'.py', '.js', '.ts', '.tsx', '.html', '.css', 
                     '.java', '.cpp', '.c', '.cs', '.go', '.php', 
                     '.rb', '.swift', '.kt', '.scala'}

def validate_github_url(url: str) -> bool:
    return url.startswith("https://github.com/") and len(url.split("/")) >= 5

def check_rate_limit():
    try:
        response = requests.get(
            "https://api.github.com/rate_limit",
            headers={"Authorization": f"token {GITHUB_TOKEN}"}
        )
        remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
        reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
        
        if remaining < 10:
            sleep_time = reset_time - time.time() + 10
            if sleep_time > 0:
                logging.warning(f"Приближаемся к лимиту. Ждем {sleep_time:.0f} сек")
                time.sleep(sleep_time)
    except Exception as e:
        logging.error(f"Ошибка проверки лимитов: {str(e)}")

def get_github_files(repo_url: str, start_date: str, end_date: str, author_email: str) -> list:
    try:
        parts = repo_url.replace("https://github.com/", "").split("/")
        owner, repo = parts[0], parts[1]
        
        commits_url = f"https://api.github.com/repos/{owner}/{repo}/commits"
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        params = {
            "since": start_date,
            "until": end_date,
            "author": author_email,  # Фильтрация по email автора
            "per_page": 100
        }
        
        check_rate_limit()
        response = requests.get(commits_url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        
        commits = response.json()
        if not isinstance(commits, list):
            logging.error(f"Неожиданный ответ от GitHub API: {commits}")
            return []
        
        files_data = []
        for commit in commits:
            commit_sha = commit.get('sha')
            if not commit_sha:
                continue
                
            commit_info = commit.get('commit', {})
            author_info = commit_info.get('author', {})
            
            # Дополнительная проверка email
            if author_info.get('email') != author_email:
                continue
                
            commit_date = author_info.get('date')
            
            # Получаем файлы коммита
            files_url = f"https://api.github.com/repos/{owner}/{repo}/commits/{commit_sha}"
            files_response = requests.get(files_url, headers=headers, timeout=10)
            
            if files_response.status_code != 200:
                continue
                
            data = files_response.json()
            if not isinstance(data, dict):
                continue
                
            for file in data.get('files', []):
                filename = file.get('filename', '')
                if not filename:
                    continue
                    
                # Пропускаем неподдерживаемые файлы
                if not any(filename.endswith(ext) for ext in ALLOWED_EXTENSIONS):
                    continue
                    
                # Получаем содержимое файла
                content_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{filename}?ref={commit_sha}"
                content_response = requests.get(content_url, headers=headers, timeout=10)
                
                if content_response.status_code != 200:
                    continue
                    
                content = content_response.json().get('content', '')
                if not content:
                    continue
                    
                try:
                    decoded_content = base64.b64decode(content).decode('utf-8', errors='ignore')
                except Exception:
                    decoded_content = "Ошибка декодирования содержимого"
                
                files_data.append({
                    'filename': filename,
                    'commit_date': commit_date,
                    'author_email': author_email,
                    'code': decoded_content
                })
        
        return files_data
        
    except Exception as e:
        logging.error(f"Ошибка получения файлов: {str(e)}")
        return []

def generate_json_report(report_id: str, files_data: list):
    try:
        report_dir = os.path.join("reports", report_id)
        os.makedirs(report_dir, exist_ok=True)
        
        report_data = {
            "report_id": report_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "files": files_data
        }
        
        json_path = os.path.join(report_dir, f"report_{report_id}.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
            
        logging.info(f"Отчет сохранен: {json_path}")
            
    except Exception as e:
        logging.error(f"Ошибка генерации отчета: {str(e)}")
        raise

def process_report(report_id: str):
    global reports
    try:
        report = next((r for r in reports if r['id'] == report_id), None)
        if not report:
            return
            
        repo_url = report['githubUrl']
        start_date, end_date = report['dateRange'].split(' - ')
        author_email = report['email']
        
        logging.info(f"Получение данных для {repo_url} ({start_date} - {end_date}), автор: {author_email}")
        
        files_data = get_github_files(repo_url, start_date, end_date, author_email)
        generate_json_report(report_id, files_data)
        
    except Exception as e:
        logging.error(f"Ошибка обработки отчета {report_id}: {str(e)}", exc_info=True)
    finally:
        for r in reports:
            if r['id'] == report_id:
                r['status'] = 'completed'

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

        report_id = str(uuid.uuid4())
        new_report = {
            'id': report_id,
            'githubUrl': github_url,
            'email': email,
            'dateRange': f"{start_date} - {end_date}",
            'status': 'processing',
            'createdAt': datetime.now(timezone.utc).isoformat()
        }
        reports.append(new_report)
        
        Thread(target=process_report, args=(report_id,)).start()
        
        return jsonify({
            "message": "Отчет добавлен в очередь",
            "reportId": report_id
        })
        
    except Exception as e:
        logging.error(f"Ошибка в generate_report: {str(e)}", exc_info=True)
        return jsonify({"error": "Внутренняя ошибка сервера"}), 500

@app.route('/api/reports', methods=['GET'])
def get_reports():
    try:
        return jsonify(reports)
    except Exception as e:
        logging.error(f"Ошибка в get_reports: {str(e)}", exc_info=True)
        return jsonify({"error": "Внутренняя ошибка сервера"}), 500

if __name__ == '__main__':
    app.run(debug=True)