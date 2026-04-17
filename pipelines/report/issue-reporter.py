#!/usr/bin/env python3
"""
Генератор отчётов в GitHub Issues
Создаёт сводку по результатам тестирования и эволюции
"""

import os
import json
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, List

class IssueReporter:
    """Создаёт отчёты в GitHub Issues"""
    
    def __init__(self, token=None, repo_owner="svend4", repo_name="info100"):
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.api_base = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
    
    def load_test_results(self) -> Dict:
        """Загружает последние результаты тестирования"""
        results_dir = Path("benchmarks/results")
        
        if not results_dir.exists():
            return None
        
        # Ищем самый свежий файл
        json_files = sorted(results_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        
        if not json_files:
            return None
        
        with open(json_files[0]) as f:
            return json.load(f)
    
    def load_evolution_log(self) -> List[Dict]:
        """Загружает лог эволюции"""
        log_dir = Path("meta/evolution-log")
        
        if not log_dir.exists():
            return []
        
        entries = []
        for log_file in log_dir.glob("*.jsonl"):
            with open(log_file) as f:
                for line in f:
                    if line.strip():
                        entries.append(json.loads(line))
        
        return entries[-10:]  # Последние 10 событий
    
    def generate_report_body(self, test_results: Dict, evolution_log: List[Dict]) -> str:
        """Генерирует тело отчёта"""
        
        # Статистика по скиллам
        tested_dir = Path("skills/tested")
        generated_dir = Path("skills/generated")
        retired_dir = Path("skills/retired")
        
        tested_count = len(list(tested_dir.glob("*.yaml"))) if tested_dir.exists() else 0
        generated_count = len(list(generated_dir.glob("*.yaml"))) if generated_dir.exists() else 0
        retired_count = len(list(retired_dir.glob("*.yaml"))) if retired_dir.exists() else 0
        
        # Результаты тестирования
        total = test_results.get("total_skills", 0) if test_results else 0
        passed = test_results.get("passed", 0) if test_results else 0
        failed = test_results.get("failed", 0) if test_results else 0
        needs_work = test_results.get("needs_work", 0) if test_results else 0
        
        body = f"""# 🤖 Ежедневный отчёт об эволюции

**Дата:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

## 📊 Статистика скиллов

| Статус | Количество |
|--------|-----------|
| ✅ Tested (fitness ≥ 0.7) | {tested_count} |
| 🔄 Generated (в разработке) | {generated_count} |
| ❌ Retired (fitness < 0.3) | {retired_count} |
| **Всего** | **{tested_count + generated_count + retired_count}** |

## 🧪 Результаты последнего тестирования

| Метрика | Значение |
|---------|----------|
| Всего скиллов протестировано | {total} |
| ✅ Успешно | {passed} |
| 🔄 Требует доработки | {needs_work} |
| ❌ Отклонено | {failed} |

"""
        
        # Детали по скиллам
        if test_results and "results" in test_results:
            body += "## 📋 Детали тестирования\n\n"
            for result in test_results["results"]:
                status_icon = "✅" if result["fitness_score"] >= 0.7 else ("🔄" if result["fitness_score"] >= 0.3 else "❌")
                body += f"**{result['skill_name']}** {status_icon}\n"
                body += f"- Fitness: `{result['fitness_score']}`\n"
                body += f"- Syntax: {'✅' if result['syntax']['passed'] else '❌'}\n"
                body += f"- Import: {'✅' if result['import']['passed'] else '❌'}\n"
                body += f"- Functional: {'✅' if result['functional']['passed'] else '❌'} ({result['functional'].get('time_ms', 0)}ms)\n\n"
        
        # Лог эволюции
        if evolution_log:
            body += "## 🧬 Последние события эволюции\n\n"
            for entry in evolution_log[-5:]:
                event_icon = "🆕" if entry.get("event") == "skill_synthesized" else "🔄"
                body += f"- {event_icon} `{entry.get('event')}` — {entry.get('skill_name', 'unknown')} ({entry.get('timestamp', 'unknown')[:10]})\n"
        
        body += f"""
## 📁 Структура знаний

```
knowledge/
├── raw/
│   ├── info1/      (534 объектов, 4 концепции)
│   └── data70/     (проекты: {', '.join(set([e.get('skill_name', '').split('-')[0] for e in evolution_log if e.get('skill_name')][:3])) or 'TetraDrone, WILOS'})
├── methods/
│   └── parallel-bidirectional.yaml
└── graph/
    └── concepts.json
```

---
*Автоматически сгенерировано агентом эволюции info100*
"""
        
        return body
    
    def create_or_update_issue(self, title: str, body: str, labels: List[str] = None):
        """Создаёт или обновляет Issue"""
        
        # Сначала ищем существующий отчёт
        search_url = f"{self.api_base}/repos/{self.repo_owner}/{self.repo_name}/issues"
        params = {"state": "open", "labels": "evolution-report", "per_page": 10}
        
        response = requests.get(search_url, headers=self.headers, params=params)
        existing_issue = None
        
        if response.status_code == 200:
            issues = response.json()
            for issue in issues:
                if "Ежедневный отчёт" in issue["title"] or "Daily Evolution Report" in issue["title"]:
                    existing_issue = issue
                    break
        
        if existing_issue:
            # Обновляем существующий
            update_url = f"{self.api_base}/repos/{self.repo_owner}/{self.repo_name}/issues/{existing_issue['number']}"
            data = {"body": body}
            
            response = requests.patch(update_url, headers=self.headers, json=data)
            
            if response.status_code == 200:
                print(f"✅ Отчёт обновлён: #{existing_issue['number']}")
                return existing_issue["number"]
            else:
                print(f"❌ Ошибка обновления: {response.status_code}")
                return None
        else:
            # Создаём новый
            data = {
                "title": title,
                "body": body,
                "labels": labels or ["evolution-report", "automated"]
            }
            
            response = requests.post(search_url, headers=self.headers, json=data)
            
            if response.status_code == 201:
                issue_number = response.json()["number"]
                print(f"✅ Отчёт создан: #{issue_number}")
                return issue_number
            else:
                print(f"❌ Ошибка создания: {response.status_code} - {response.text[:200]}")
                return None
    
    def run(self):
        """Главный пайплайн отчётности"""
        print("📝 Генерация отчёта...")
        
        test_results = self.load_test_results()
        evolution_log = self.load_evolution_log()
        
        title = f"🤖 Ежедневный отчёт об эволюции — {datetime.now().strftime('%Y-%m-%d')}"
        body = self.generate_report_body(test_results, evolution_log)
        
        issue_number = self.create_or_update_issue(title, body)
        
        if issue_number:
            # Сохраняем мета-информацию
            meta = {
                "issue_number": issue_number,
                "created_at": datetime.now().isoformat(),
                "test_results_loaded": test_results is not None,
                "evolution_events": len(evolution_log)
            }
            
            with open("meta/last-report.json", "w") as f:
                json.dump(meta, f, indent=2)
        
        return issue_number

if __name__ == "__main__":
    import sys
    
    token = os.getenv("GITHUB_TOKEN")
    if len(sys.argv) > 1:
        token = sys.argv[1]
    
    reporter = IssueReporter(token=token)
    issue_number = reporter.run()
    
    if issue_number:
        print(json.dumps({"status": "success", "issue_number": issue_number}, indent=2))
    else:
        print(json.dumps({"status": "error"}, indent=2))
        sys.exit(1)
