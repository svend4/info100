#!/usr/bin/env python3
"""
Агент-сборщик для svend4/data70
Извлекает TetraDrone, WILOS и другие проекты
Создаёт связи с info1 для кросс-поллинации
"""

import os
import sys
import json
import yaml
import requests
from pathlib import Path
from datetime import datetime

REPO_OWNER = "svend4"
REPO_NAME = "data70"
TARGET_DIR = Path("knowledge/raw/data70")
API_BASE = "https://api.github.com"

class Data70Collector:
    """Сборщик для data70 — фокус на проектах, метриках, паттернах"""
    
    def __init__(self, token=None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.headers = {}
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"
        self.headers["Accept"] = "application/vnd.github.v3+json"
        self.projects_found = []
        
    def fetch_repo_structure(self):
        """Получает структуру репозитория"""
        url = f"{API_BASE}/repos/{REPO_OWNER}/{REPO_NAME}/git/trees/main?recursive=1"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            return response.json().get("tree", [])
        elif response.status_code == 404:
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
            return base64.b64decode(content).decode("utf-8", errors='replace')
        return None
    
    def extract_projects(self, content):
        """Извлекает упоминания проектов из текста"""
        projects = []
        keywords = ["TetraDrone", "WILOS", "Leonardo", "AI", "AGI", "робот", "drone"]
        
        for keyword in keywords:
            if keyword.lower() in content.lower():
                projects.append(keyword)
        
        return list(set(projects))
    
    def extract_conversations_summary(self, content):
        """Создаёт краткую сводку из содержимого"""
        lines = content.split("\n")[:50]  # Первые 50 строк
        return {
            "preview": "\n".join(lines[:10]),
            "total_lines": len(content.split("\n")),
            "extracted_at": datetime.now().isoformat()
        }
    
    def update_graph_links(self):
        """Обновляет граф связей между info1 и data70"""
        graph_file = Path("knowledge/graph/concepts.json")
        
        if graph_file.exists():
            with open(graph_file) as f:
                graph = json.load(f)
        else:
            graph = {"version": "1.0.0", "nodes": [], "edges": [], "last_updated": ""}
        
        # Добавляем ноды для data70
        data70_nodes = [
            {"id": "data70", "type": "repository", "name": "svend4/data70"},
            {"id": "tetradron", "type": "project", "name": "TetraDrone"},
            {"id": "wilos", "type": "project", "name": "WILOS"}
        ]
        
        for node in data70_nodes:
            if not any(n["id"] == node["id"] for n in graph["nodes"]):
                graph["nodes"].append(node)
        
        # Добавляем связи
        edges = [
            {"from": "tetradron", "to": "parallel-bidirectional", "relation": "implements", "strength": 0.8},
            {"from": "wilos", "to": "parallel-bidirectional", "relation": "uses", "strength": 0.7},
            {"from": "data70", "to": "info1", "relation": "extends", "strength": 0.9}
        ]
        
        for edge in edges:
            if not any(e["from"] == edge["from"] and e["to"] == edge["to"] for e in graph["edges"]):
                graph["edges"].append(edge)
        
        graph["last_updated"] = datetime.now().isoformat()
        
        with open(graph_file, "w", encoding="utf-8") as f:
            json.dump(graph, f, indent=2, ensure_ascii=False)
        
        print(f"🔗 Граф обновлен: {len(graph['nodes'])} нод, {len(graph['edges'])} связей")
    
    def run(self):
        """Главный пайплайн сбора"""
        print(f"🚀 Запуск сбора {REPO_OWNER}/{REPO_NAME}")
        
        TARGET_DIR.mkdir(parents=True, exist_ok=True)
        
        tree = self.fetch_repo_structure()
        print(f"📁 Найдено {len(tree)} объектов")
        
        # Ограничиваем для производительности
        markdown_files = [item for item in tree if item["path"].endswith(".md")][:20]
        json_files = [item for item in tree if item["path"].endswith(".json")][:10]
        
        all_projects = []
        processed_files = []
        
        # Обрабатываем markdown
        for item in markdown_files:
            path = item["path"]
            content = self.fetch_file_content(path)
            if content:
                projects = self.extract_projects(content)
                all_projects.extend(projects)
                processed_files.append({
                    "path": path,
                    "projects_found": projects,
                    "size": len(content)
                })
                
                # Сохраняем контент
                file_dir = TARGET_DIR / "content" / Path(path).parent
                file_dir.mkdir(parents=True, exist_ok=True)
                with open(file_dir / Path(path).name, "w", encoding="utf-8") as f:
                    f.write(content)
        
        # Обрабатываем JSON
        conversations_data = []
        for item in json_files:
            path = item["path"]
            content = self.fetch_file_content(path)
            if content:
                try:
                    data = json.loads(content)
                    summary = {
                        "path": path,
                        "type": "json_data",
                        "keys": list(data.keys()) if isinstance(data, dict) else f"list[{len(data)}]"
                    }
                    conversations_data.append(summary)
                    
                    # Сохраняем
                    with open(TARGET_DIR / "content" / path, "w", encoding="utf-8") as f:
                        f.write(content)
                except:
                    pass
        
        # Уникальные проекты
        unique_projects = list(set(all_projects))
        
        structure = {
            "repo": f"{REPO_OWNER}/{REPO_NAME}",
            "collected_at": datetime.now().isoformat(),
            "total_objects": len(tree),
            "markdown_processed": len(markdown_files),
            "json_processed": len(json_files),
            "projects_found": unique_projects,
            "files": processed_files[:10]  # Первые 10 для примера
        }
        
        with open(TARGET_DIR / ".structure.json", "w", encoding="utf-8") as f:
            json.dump(structure, f, indent=2, ensure_ascii=False)
        
        # Создаём мета
        meta = {
            "agent": "data70-collector",
            "version": "1.0.0",
            "source": f"{REPO_OWNER}/{REPO_NAME}",
            "collected_at": datetime.now().isoformat(),
            "projects": unique_projects,
            "structure": structure
        }
        
        with open(TARGET_DIR / ".meta.yaml", "w", encoding="utf-8") as f:
            yaml.dump(meta, f, allow_unicode=True)
        
        # Обновляем граф
        self.update_graph_links()
        
        print(f"✅ Сбор завершен. Проекты: {', '.join(unique_projects) if unique_projects else 'none'}")
        return meta

if __name__ == "__main__":
    token = os.getenv("GITHUB_TOKEN")
    if len(sys.argv) > 1:
        token = sys.argv[1]
    
    collector = Data70Collector(token=token)
    result = collector.run()
    print(json.dumps(result, indent=2, ensure_ascii=False))
