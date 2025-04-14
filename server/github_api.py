import base64
import time
import requests
import logging
from config import Config
from typing import List, Dict

logger = logging.getLogger(__name__)

def check_rate_limit():
    try:
        response = requests.get(
            "https://api.github.com/rate_limit",
            headers={"Authorization": f"token {Config.GITHUB_TOKEN}"}
        )
        remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
        reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
        
        if remaining < 10:
            sleep_time = reset_time - time.time() + 10
            if sleep_time > 0:
                logger.warning(f"Приближаемся к лимиту. Ждем {sleep_time:.0f} сек")
                time.sleep(sleep_time)
    except Exception as e:
        logger.error(f"Ошибка проверки лимитов: {str(e)}")

def get_github_files(repo_url: str, start_date: str, end_date: str, author_email: str) -> List[Dict]:
    try:
        parts = repo_url.replace("https://github.com/", "").split("/")
        owner, repo = parts[0], parts[1]
        
        commits_url = f"https://api.github.com/repos/{owner}/{repo}/commits"
        headers = {
            "Authorization": f"token {Config.GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        params = {
            "since": start_date,
            "until": end_date,
            "author": author_email,
            "per_page": 100
        }
        
        check_rate_limit()
        response = requests.get(commits_url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        
        commits = response.json()
        if not isinstance(commits, list):
            logger.error(f"Неожиданный ответ от GitHub API: {commits}")
            return []
        
        files_data = []
        for commit in commits:
            commit_sha = commit.get('sha')
            if not commit_sha:
                continue
                
            commit_info = commit.get('commit', {})
            author_info = commit_info.get('author', {})
            
            if author_info.get('email') != author_email:
                continue
                
            commit_date = author_info.get('date')
            
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
                    
                if not any(filename.endswith(ext) for ext in Config.ALLOWED_EXTENSIONS):
                    continue
                    
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
        logger.error(f"Ошибка получения файлов: {str(e)}")
        return []