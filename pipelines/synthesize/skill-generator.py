#!/usr/bin/env python3
"""
Агент синтеза — создает новые скиллы из методологий
Берет методологию из knowledge/methods/ → генерирует скилл в skills/generated/
"""

import yaml
import json
from pathlib import Path
from datetime import datetime
from string import Template

class SkillSynthesizer:
    """Синтезирует скиллы из абстрактных методологий"""
    
    def __init__(self):
        self.methods_dir = Path("knowledge/methods")
        self.output_dir = Path("skills/generated")
        self.template_path = Path("skills/templates/skill-template.yaml")
        
    def load_methodology(self, method_name):
        """Загружает методологию"""
        method_file = self.methods_dir / f"{method_name}.yaml"
        if method_file.exists():
            with open(method_file) as f:
                return yaml.safe_load(f)
        return None
    
    def generate_skill(self, method_name, skill_name, description=""):
        """Генерирует скилл из методологии"""
        
        # Читаем шаблон
        with open(self.template_path) as f:
            template = Template(f.read())
        
        # Заполняем
        skill_content = template.substitute(
            skill_name=skill_name,
            description=description or f"Generated from {method_name}",
            parent_method=method_name,
            timestamp=datetime.now().isoformat(),
            input_spec="text",
            output_spec="structured_data",
            code_block="# TODO: Implement based on methodology"
        )
        
        # Сохраняем
        self.output_dir.mkdir(parents=True, exist_ok=True)
        skill_file = self.output_dir / f"{skill_name}.yaml"
        
        with open(skill_file, "w") as f:
            f.write(skill_content)
        
        print(f"✅ Сгенерирован скилл: {skill_file}")
        return skill_file
    
    def run(self, method_name, skill_name):
        """Главный пайплайн"""
        print(f"🧬 Синтез: {method_name} → {skill_name}")
        
        method = self.load_methodology(method_name)
        if not method:
            print(f"❌ Методология {method_name} не найдена")
            return None
        
        skill_file = self.generate_skill(method_name, skill_name)
        return skill_file

if __name__ == "__main__":
    import sys
    
    synthesizer = SkillSynthesizer()
    
    if len(sys.argv) >= 3:
        method_name = sys.argv[1]
        skill_name = sys.argv[2]
    else:
        method_name = "parallel-bidirectional"
        skill_name = "parallel-agent-v1"
    
    synthesizer.run(method_name, skill_name)
