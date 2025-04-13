import os
import uuid
import base64
import requests
from flask_cors import CORS
from threading import Thread
from datetime import datetime, timezone
from flask import Flask, request, jsonify

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})

if not os.path.exists("reports"):
    os.makedirs("reports")

reports = []

def validate_github_url(url: str) -> bool:
    return url.startswith("https://github.com/") and len(url.split("/")) >= 5

def get_github_files(repo_url: str, start_date: str, end_date: str) -> list:
    parts = repo_url.replace("https://github.com/", "").split("/")
    owner, repo = parts[0], parts[1]
    
    commits_url = f"https://api.github.com/repos/{owner}/{repo}/commits"
    headers = {
        #"Authorization": f"token {os.getenv('GITHUB_TOKEN')}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    params = {
        "since": start_date,
        "until": end_date,
        "per_page": 100
    }
    
    response = requests.get(commits_url, headers=headers, params=params)
    
    if response.status_code != 200:
        raise Exception(f"Ошибка доступа к репозиторию: {response.status_code}")
    
    commits = response.json()
    files_data = []
    
    for commit in commits:
        commit_sha = commit['sha']
        commit_date = commit['commit']['author']['date']
        author_email = commit['commit']['author']['email']
        
        files_url = f"https://api.github.com/repos/{owner}/{repo}/commits/{commit_sha}"
        files_response = requests.get(files_url, headers=headers)

        if files_response.status_code != 200:
            continue
        
        for file in files_response.json().get('files', []):
            filename = file['filename']
            
            content_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{filename}?ref={commit_sha}"
            content_response = requests.get(content_url, headers=headers)
            
            code = "Ошибка получения содержимого"
            if content_response.status_code == 200:
                content = content_response.json().get('content', '')
                try:
                    decoded_content = base64.b64decode(content).decode('utf-8', errors='ignore')
                    code = decoded_content
                except Exception as e:
                    print(f"Ошибка декодирования файла {filename}: {str(e)}")
                    code = "Ошибка декодирования содержимого"
            
            files_data.append({
                'filename': filename,
                'commit_date': commit_date,
                'author_email': author_email,
                'code': code
            })
    
    return files_data

def generate_txt_report(report_id: str, files_data: list):
    report_dir = os.path.join("reports", report_id)
    os.makedirs(report_dir, exist_ok=True)
    
    for file_data in files_data:
        filename = os.path.basename(file_data['filename'])
        safe_filename = "".join(c if c.isalnum() else "_" for c in filename)
        file_path = os.path.join(report_dir, f"{safe_filename}.txt")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"Файл: {file_data['filename']}\n")
            f.write(f"Дата коммита: {file_data['commit_date']}\n")
            f.write(f"Автор: {file_data['author_email']}\n")
            f.write("---- Код ----\n")
            f.write(file_data['code'])
            f.write("\n" + "="*40 + "\n")

def process_report(report_id: str):
    global reports
    report = next((r for r in reports if r['id'] == report_id), None)
    if not report:
        return

    try:
        repo_url = report['githubUrl']
        start_date, end_date = report['dateRange'].split(' - ')
        
        files_data = get_github_files(repo_url, start_date, end_date)
        
        generate_txt_report(report_id, files_data)
        
    except Exception as e:
        print(f"Ошибка обработки отчета {report_id}: {str(e)}")
    
    finally:
        report['status'] = 'completed'

@app.route('/api/generate-report', methods=['POST'])
def generate_report():
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

@app.route('/api/reports', methods=['GET'])
def get_reports():
    return jsonify(reports)

if __name__ == '__main__':
    app.run(debug=True)