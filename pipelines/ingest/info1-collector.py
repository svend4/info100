#!/usr/bin/env python3
"""
Агент-сборщик для svend4/info1
Забирает структуру, методологии, паттерны из репозитория
и преобразует в структурированный вид для info100
"""

import os
import sys
import json
import yaml
import requests
from pathlib import Path
from datetime import datetime

# Конфигурация
REPO_OWNER = "svend4"
REPO_NAME = "info1"
TARGET_DIR = Path("knowledge/raw/info1")
API_BASE = "https://api.github.com"

class Info1Collector:
    """Специализированный сборщик для info1 — извлекает методологию параллельного развития"""
    
    def __init__(self, token=None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.headers = {}
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"
        self.headers["Accept"] = "application/vnd.github.v3+json"
        
    def fetch_repo_structure(self):
        """Получает структуру репозитория через GitHub API"""
        url = f"{API_BASE}/repos/{REPO_OWNER}/{REPO_NAME}/git/trees/main?recursive=1"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            return response.json().get("tree", [])
        elif response.status_code == 404:
            # Пробуем master
            url = f"{API_BASE}/repos/{REPO_OWNER}/{REPO_NAME}/git/trees/master?recursive=1"
            response = requests.get(url, headers=self.headers)
            return response.json().get("tree", [])
        else:
            print(f"❌ Ошибка: {response.status_code}")
            return []
    
    def fetch_file_content(self, path):
        """Забирает содержимое файла"""
        url = f"{API_BASE}/repos/{REPO_OWNER}/{REPO_NAME}/contents/{path}"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            import base64
            content = response.json().get("content", "")
            return base64.b64decode(content).decode("utf-8")
        return None
    
    def extract_methodology(self, readme_content):
        """Извлекает методологию параллельного двунаправленного развития"""
        methodology = {
            "name": "Параллельное двунаправленное развитие",
            "source": "svend4/info1",
            "extracted_at": datetime.now().isoformat(),
            "concepts": [],
            "patterns": []
        }
        
        if "параллельного двунаправленного" in readme_content.lower():
            methodology["detected"] = True
            
        # Простая эвристика для извлечения секций
        lines = readme_content.split("\n")
        for i, line in enumerate(lines):
            if line.startswith("#") and "методолог" in line.lower():
                methodology["concepts"].append({
                    "title": line.strip("# "),
                    "line": i
                })
        
        return methodology
    
    def run(self):
        """Главный пайплайн сбора"""
        print(f"🚀 Запуск сбора {REPO_OWNER}/{REPO_NAME}")
        
        # Создаем директории
        TARGET_DIR.mkdir(parents=True, exist_ok=True)
        
        # Получаем структуру
        tree = self.fetch_repo_structure()
        print(f"📁 Найдено {len(tree)} объектов")
        
        structure = {
            "repo": f"{REPO_OWNER}/{REPO_NAME}",
            "collected_at": datetime.now().isoformat(),
            "total_files": 0,
            "total_dirs": 0,
            "markdown_files": [],
            "code_files": [],
            "other_files": []
        }
        
        # Классифицируем файлы
        for item in tree:
            path = item["path"]
            item_type = item["type"]
            
            if item_type == "blob":
                structure["total_files"] += 1
                if path.endswith(".md"):
                    structure["markdown_files"].append(path)
                elif path.endswith((".py", ".js", ".yaml", ".json")):
                    structure["code_files"].append(path)
                else:
                    structure["other_files"].append(path)
            elif item_type == "tree":
                structure["total_dirs"] += 1
        
        # Сохраняем структуру
        with open(TARGET_DIR / ".structure.json", "w", encoding="utf-8") as f:
            json.dump(structure, f, indent=2, ensure_ascii=False)
        
        # Забираем README
        readme_content = self.fetch_file_content("README.md")
        if readme_content:
            with open(TARGET_DIR / "README.md", "w", encoding="utf-8") as f:
                f.write(readme_content)
            
            # Извлекаем методологию
            methodology = self.extract_methodology(readme_content)
            with open(TARGET_DIR / ".methodology.json", "w", encoding="utf-8") as f:
                json.dump(methodology, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Методология извлечена: {len(methodology['concepts'])} концепций")
        
        # Создаем мета-файл
        meta = {
            "agent": "info1-collector",
            "version": "1.0.0",
            "source": f"{REPO_OWNER}/{REPO_NAME}",
            "collected_at": datetime.now().isoformat(),
            "structure": structure
        }
        
        with open(TARGET_DIR / ".meta.yaml", "w", encoding="utf-8") as f:
            yaml.dump(meta, f, allow_unicode=True)
        
        print(f"✅ Сбор завершен. Данные в {TARGET_DIR}")
        return meta

if __name__ == "__main__":
    token = os.getenv("GITHUB_TOKEN")
    if len(sys.argv) > 1:
        token = sys.argv[1]
    
    collector = Info1Collector(token=token)
    result = collector.run()
    print(json.dumps(result, indent=2, ensure_ascii=False))
