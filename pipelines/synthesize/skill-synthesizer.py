#!/usr/bin/env python3
"""
Полноценный синтезатор скиллов из методологий
Берет методологии из knowledge/methods/ + данные из raw/
Генерирует реальные скиллы в skills/generated/
"""

import yaml
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

class SkillSynthesizer:
    """Синтезирует скиллы из методологий с учетом связей из графа"""
    
    def __init__(self):
        self.methods_dir = Path("knowledge/methods")
        self.raw_dir = Path("knowledge/raw")
        self.output_dir = Path("skills/generated")
        self.tested_dir = Path("skills/tested")
        self.retired_dir = Path("skills/retired")
        self.graph_file = Path("knowledge/graph/concepts.json")
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.tested_dir.mkdir(parents=True, exist_ok=True)
        self.retired_dir.mkdir(parents=True, exist_ok=True)
    
    def load_methodology(self, method_name: str) -> Dict:
        """Загружает методологию"""
        method_file = self.methods_dir / f"{method_name}.yaml"
        if method_file.exists():
            with open(method_file) as f:
                return yaml.safe_load(f)
        return None
    
    def load_graph(self) -> Dict:
        """Загружает граф связей"""
        if self.graph_file.exists():
            with open(self.graph_file) as f:
                return json.load(f)
        return {"nodes": [], "edges": []}
    
    def find_related_concepts(self, method_name: str, graph: Dict) -> List[str]:
        """Находит связанные концепции через граф"""
        related = []
        for edge in graph.get("edges", []):
            if edge["from"] == method_name:
                related.append(edge["to"])
            elif edge["to"] == method_name:
                related.append(edge["from"])
        return related
    
    def generate_skill_code(self, method: Dict, related: List[str]) -> str:
        """Генерирует Python-код на основе методологии"""
        concepts = method.get("concepts", [])
        patterns = method.get("patterns", [])
        
        code_lines = [
            "\"\"\"",
            f"Скилл: {method.get('name', 'Unknown')}",
            f"Сгенерирован: {datetime.now().isoformat()}",
            f"На основе: {method.get('source', 'unknown')}",
            "\"\"\"",
            "",
            "from typing import Dict, List, Any, Optional",
            "from dataclasses import dataclass",
            "from datetime import datetime",
            "",
            f"# Концепции: {', '.join([c.get('name', 'unknown') for c in concepts[:3]])}",
            "",
            "@dataclass",
            "class AgentConfig:",
            "    name: str",
            "    version: str = '1.0.0'",
            "    capabilities: List[str] = None",
            "",
            f"class {method.get('name', 'Skill').replace(' ', '').replace('-', '')}Skill:",
            "    \"\"\"",
            f"    {method.get('description', 'Generated skill')}",
            "    \"\"\"",
            "",
            "    def __init__(self, config: AgentConfig = None):",
            "        self.config = config or AgentConfig(name='default')",
            f"        self.patterns = {patterns}",
            "        self.initialized_at = datetime.now()",
            "",
            "    def process(self, input_data: Dict) -> Dict:",
            "        \"\"\"Главный метод обработки\"\"\"",
            "        result = {",
            "            'status': 'processed',",
            "            'timestamp': datetime.now().isoformat(),",
            "            'methodology': self.config.name,",
            "            'patterns_applied': len(self.patterns)",
            "        }",
            "        return result",
            "",
            "    def validate(self) -> bool:",
            "        \"\"\"Валидация конфигурации\"\"\"",
            "        return self.config is not None and self.config.name",
            "",
            f"# Связанные концепции: {', '.join(related[:5]) if related else 'none'}",
        ]
        
        return "\n".join(code_lines)
    
    def generate_skill_yaml(self, method_name: str, skill_name: str, 
                            description: str = "") -> Dict:
        """Генерирует полный YAML скилла"""
        
        method = self.load_methodology(method_name)
        if not method:
            return None
        
        graph = self.load_graph()
        related = self.find_related_concepts(method_name, graph)
        
        code = self.generate_skill_code(method, related)
        
        # Генерируем ID
        content_hash = hashlib.md5(
            f"{method_name}:{skill_name}:{datetime.now().isoformat()}".encode()
        ).hexdigest()[:8]
        
        skill = {
            "name": skill_name,
            "version": "0.1.0",
            "skill_id": f"{skill_name}-{content_hash}",
            "type": "generated",
            "description": description or f"Generated from {method_name}",
            "origin": {
                "method": method_name,
                "methodology_source": method.get("source", "unknown"),
                "synthesized_from": related,
                "parent_agents": ["info1-collector", "data70-collector"],
                "created_at": datetime.now().isoformat()
            },
            "genome": {
                "generation": 1,
                "mutations": ["initial_synthesis"],
                "fitness_score": None,
                "last_evaluated": None
            },
            "interface": {
                "input": "dict",
                "output": "dict",
                "required_fields": ["action"],
                "optional_fields": ["context", "parameters"]
            },
            "implementation": {
                "language": "python",
                "code": code,
                "dependencies": ["typing", "dataclasses", "datetime"],
                "entry_point": f"{skill_name}.Skill.process"
            },
            "tests": {
                "unit_tests": [],
                "integration_tests": [],
                "benchmark_results": {}
            },
            "status": "generated"
        }
        
        return skill
    
    def save_skill(self, skill: Dict, filename: str = None):
        """Сохраняет скилл в файл"""
        if not filename:
            filename = f"{skill['name']}.yaml"
        
        skill_file = self.output_dir / filename
        with open(skill_file, "w", encoding="utf-8") as f:
            yaml.dump(skill, f, allow_unicode=True, sort_keys=False)
        
        # Также сохраняем Python файл
        py_file = self.output_dir / f"{skill['name']}.py"
        with open(py_file, "w", encoding="utf-8") as f:
            f.write(skill["implementation"]["code"])
        
        print(f"✅ Скилл сохранен: {skill_file} + {py_file}")
        return skill_file
    
    def run(self, method_name: str, skill_name: str, description: str = ""):
        """Главный пайплайн синтеза"""
        print(f"🧬 Синтез: {method_name} → {skill_name}")
        
        skill = self.generate_skill_yaml(method_name, skill_name, description)
        if not skill:
            print(f"❌ Методология {method_name} не найдена")
            return None
        
        skill_file = self.save_skill(skill)
        
        # Создаем эксперимент-запись
        self.log_synthesis(skill)
        
        return skill
    
    def log_synthesis(self, skill: Dict):
        """Логирует синтез в meta/evolution-log/"""
        log_dir = Path("meta/evolution-log")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event": "skill_synthesized",
            "skill_id": skill["skill_id"],
            "skill_name": skill["name"],
            "method": skill["origin"]["method"],
            "status": "success"
        }
        
        log_file = log_dir / f"{datetime.now().strftime('%Y%m%d')}-synthesis.jsonl"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

if __name__ == "__main__":
    import sys
    
    synthesizer = SkillSynthesizer()
    
    if len(sys.argv) >= 3:
        method_name = sys.argv[1]
        skill_name = sys.argv[2]
        description = sys.argv[3] if len(sys.argv) > 3 else ""
    else:
        method_name = "parallel-bidirectional"
        skill_name = "parallel-agent-v1"
        description = "Agent implementing parallel bidirectional methodology"
    
    skill = synthesizer.run(method_name, skill_name, description)
    if skill:
        print(json.dumps({"skill_id": skill["skill_id"], "status": "generated"}, indent=2))
