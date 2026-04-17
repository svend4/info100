#!/usr/bin/env python3
"""
Инициализатор нового эксперимента
Создает структуру для тестирования гипотезы
"""

import os
import yaml
import json
from pathlib import Path
from datetime import datetime
from string import Template

class ExperimentInitializer:
    """Создает структуру нового эксперимента"""
    
    def __init__(self):
        self.experiments_dir = Path("experiments/active")
        self.template = Template("""# Эксперимент: $name

## Метаданные
- **ID**: $exp_id
- **Создан**: $timestamp
- **Гипотеза**: $hypothesis
- **Агенты**: $agents
- **Статус**: active

## Цель
$goal

## Методология
$methodology

## Ожидаемые результаты
$expected_results

## Ход работы

### $timestamp — Инициализация
- Создана структура эксперимента
- Назначены агенты

## Артефакты
- `artifacts/` — сгенерированные файлы
- `logs/` — логи выполнения
- `results/` — результаты тестирования

## Связи
- Методология: $method_link
- Скиллы: $skills_link
""")
    
    def create_experiment(self, name, hypothesis, agents, goal, methodology):
        """Создает новый эксперимент"""
        
        exp_id = f"{datetime.now().strftime('%Y%m%d')}-{name.lower().replace(' ', '-')}"
        exp_dir = self.experiments_dir / exp_id
        
        # Создаем директории
        (exp_dir / "artifacts").mkdir(parents=True, exist_ok=True)
        (exp_dir / "logs").mkdir(exist_ok=True)
        (exp_dir / "results").mkdir(exist_ok=True)
        
        # Создаем README
        readme_content = self.template.substitute(
            name=name,
            exp_id=exp_id,
            timestamp=datetime.now().isoformat(),
            hypothesis=hypothesis,
            agents=", ".join(agents),
            goal=goal,
            methodology=methodology,
            expected_results="TODO: заполнить после выполнения",
            method_link=f"[Методология](../../knowledge/methods/)",
            skills_link=f"[Скиллы](../../skills/generated/)"
        )
        
        with open(exp_dir / "README.md", "w") as f:
            f.write(readme_content)
        
        # Создаем мета-файл
        meta = {
            "id": exp_id,
            "name": name,
            "hypothesis": hypothesis,
            "agents": agents,
            "created_at": datetime.now().isoformat(),
            "status": "active",
            "artifacts": [],
            "results": {}
        }
        
        with open(exp_dir / ".meta.yaml", "w") as f:
            yaml.dump(meta, f, allow_unicode=True)
        
        print(f"🔬 Эксперимент создан: {exp_dir}")
        return exp_dir

if __name__ == "__main__":
    import sys
    
    initializer = ExperimentInitializer()
    
    if len(sys.argv) >= 2:
        name = sys.argv[1]
    else:
        name = "test-methodology-synthesis"
    
    exp_dir = initializer.create_experiment(
        name=name,
        hypothesis="Можно ли автоматически синтезировать скилл из методологии svend4/info1?",
        agents=["info1-collector", "skill-synthesizer"],
        goal="Создать рабочий скилл на основе методологии параллельного развития",
        methodology="Параллельное двунаправленное развитие"
    )
    
    print(f"🚀 Готов к запуску: {exp_dir}")
