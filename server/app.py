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

load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
if not GITHUB_TOKEN:
    logging.error("GITHUB_TOKEN не найден в .env файле")
    exit("Ошибка: GITHUB_TOKEN не установлен. Создайте .env файл с GITHUB_TOKEN.")

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

ALLOWED_EXTENSIONS = {'.py', '.js', '.ts', '.tsx', '.html', '.css', '.java', '.cpp', '.c', '.cs', '.css', '.go', '.php', '.rb', '.swift', '.kt', '.scala'}

def validate_github_url(url: str) -> bool:
    if not url.startswith("https://github.com/"):
        logging.warning(f"Некорректный URL: {url} - неверный формат")
        return False
    parts = url.replace("https://github.com/", "").split("/")
    if len(parts) < 2:
        logging.warning(f"Некорректный URL: {url} - не хватает компонентов")
        return False
    return True

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

def get_github_files(repo_url: str, start_date: str, end_date: str) -> list:
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
            "per_page": 100
        }
        
        check_rate_limit()
        
        response = requests.get(commits_url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        
        commits = response.json()
        files_data = []
        
        for commit in commits:
            commit_sha = commit.get('sha')
            if not commit_sha:
                logging.warning(f"SHA отсутствует в коммите: {commit}")
                continue
                
            commit_date = commit['commit']['author']['date']
            author_email = commit['commit']['author']['email']
            
            files_url = f"https://api.github.com/repos/{owner}/{repo}/commits/{commit_sha}"
            files_response = requests.get(files_url, headers=headers, timeout=10)
            
            if files_response.status_code != 200:
                logging.error(f"Ошибка {files_response.status_code} при получении коммита {commit_sha}")
                continue
                
            data = files_response.json()
            if not isinstance(data, dict):
                logging.error(f"Неожиданный формат ответа для коммита {commit_sha}: {type(data)}")
                continue
                
            for file in data.get('files', []):
                filename = file.get('filename', 'unknown')
                
                if not any(filename.endswith(ext) for ext in ALLOWED_EXTENSIONS):
                    logging.debug(f"Пропущен файл {filename}: недопустимое расширение")
                    continue
                
                if '/' in filename and '.' not in filename.split('/')[-1]:
                    logging.debug(f"Пропущена директория: {filename}")
                    continue
                    
                content_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{filename}?ref={commit_sha}"
                
                try:
                    content_response = requests.get(content_url, headers=headers, timeout=10)
                    content_response.raise_for_status()
                    
                    content = content_response.json().get('content', '')
                    if not content:
                        logging.warning(f"Пустое содержимое для файла: {filename}")
                        continue
                        
                    decoded_content = base64.b64decode(content).decode('utf-8', errors='ignore')
                    
                    files_data.append({
                        'filename': filename,
                        'commit_date': commit_date,
                        'author_email': author_email,
                        'code': decoded_content
                    })
                    
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 404:
                        logging.warning(f"Файл {filename} не найден в коммите {commit_sha}")
                    else:
                        logging.error(f"Ошибка получения содержимого {filename}: {str(e)}")
                except Exception as e:
                    logging.error(f"Ошибка обработки файла {filename}: {str(e)}")
        
        return files_data
        
    except requests.exceptions.RequestException as e:
        logging.error(f"Сетевая ошибка при работе с GitHub API: {str(e)}")
        raise
    except Exception as e:
        logging.error(f"Непредвиденная ошибка: {str(e)}")
        raise

def generate_json_report(report_id: str, files_data: list):
    try:
        report_dir = os.path.join("reports", report_id)
        os.makedirs(report_dir, exist_ok=True)
        
        # Формируем структуру JSON
        report_data = {
            "report_id": report_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "files": []
        }
        
        for file_data in files_data:
            # Добавляем метаданные и содержимое файлов
            report_data["files"].append({
                "filename": file_data.get('filename', 'N/A'),
                "commit_date": file_data.get('commit_date', 'N/A'),
                "author_email": file_data.get('author_email', 'N/A'),
                "code": file_data.get('code', 'Ошибка: содержимое недоступно'),
                "extension": os.path.splitext(file_data.get('filename', ''))[1]
            })
        
        # Сохраняем в JSON файл
        json_filename = os.path.join(report_dir, f"report_{report_id}.json")
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
            
        logging.info(f"JSON-отчет сохранен: {json_filename}")
            
    except Exception as e:
        logging.error(f"Ошибка генерации JSON-отчета {report_id}: {str(e)}")
        raise

def process_report(report_id: str):
    global reports
    try:
        logging.info(f"Начата обработка отчета {report_id}")
        report = next((r for r in reports if r['id'] == report_id), None)
        if not report:
            logging.error(f"Отчет {report_id} не найден")
            return

        repo_url = report['githubUrl']
        start_date, end_date = report['dateRange'].split(' - ')
        
        logging.info(f"Получение данных для {repo_url} ({start_date} - {end_date})")
        files_data = get_github_files(repo_url, start_date, end_date)
        
        logging.info(f"Генерация отчета для {report_id}")
        generate_json_report(report_id, files_data)
        
    except Exception as e:
        logging.error(f"Критическая ошибка обработки отчета {report_id}: {str(e)}", exc_info=True)
    finally:
        for r in reports:
            if r['id'] == report_id:
                r['status'] = 'completed'
        logging.info(f"Обработка отчета {report_id} завершена")

@app.route('/api/generate-report', methods=['POST'])
def generate_report():
    try:
        data = request.json
        github_url = data.get('githubUrl')
        email = data.get('email')
        start_date = data.get('startDate')
        end_date = data.get('endDate')
        
        if not validate_github_url(github_url):
            return jsonify({"error": "Некорректный GitHub URL"}), 400
            
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