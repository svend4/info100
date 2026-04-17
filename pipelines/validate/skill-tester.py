#!/usr/bin/env python3
"""
Полноценный тестер скиллов с обновлением fitness_score
Запускает тесты, оценивает, обновляет YAML, перемещает между статусами
"""

import yaml
import json
import time
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

class SkillTester:
    """Тестирует скиллы и обновляет их fitness_score"""
    
    def __init__(self):
        self.generated_dir = Path("skills/generated")
        self.tested_dir = Path("skills/tested")
        self.retired_dir = Path("skills/retired")
        self.results_dir = Path("benchmarks/results")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        self.tested_dir.mkdir(parents=True, exist_ok=True)
        self.retired_dir.mkdir(parents=True, exist_ok=True)
    
    def load_skill(self, skill_file: Path) -> Dict:
        """Загружает скилл из YAML"""
        with open(skill_file) as f:
            return yaml.safe_load(f)
    
    def save_skill(self, skill: Dict, filepath: Path):
        """Сохраняет скилл в YAML"""
        with open(filepath, "w", encoding="utf-8") as f:
            yaml.dump(skill, f, allow_unicode=True, sort_keys=False)
    
    def run_syntax_test(self, skill: Dict) -> Tuple[bool, str]:
        """Тест 1: Проверка синтаксиса Python-кода"""
        code = skill.get("implementation", {}).get("code", "")
        
        try:
            compile(code, "<string>", "exec")
            return True, "Syntax OK"
        except SyntaxError as e:
            return False, f"Syntax Error: {e}"
    
    def run_import_test(self, skill: Dict) -> Tuple[bool, str]:
        """Тест 2: Проверка импорта модуля"""
        py_file = self.generated_dir / f"{skill['name']}.py"
        
        if not py_file.exists():
            return False, "Python file not found"
        
        try:
            # Пробуем импортировать
            spec = __import__("importlib.util").util.spec_from_file_location(
                skill["name"], py_file
            )
            module = __import__("importlib.util").util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return True, "Import OK"
        except Exception as e:
            return False, f"Import Error: {str(e)[:100]}"
    
    def run_functional_test(self, skill: Dict) -> Tuple[bool, str, float]:
        """Тест 3: Функциональная проверка process()"""
        py_file = self.generated_dir / f"{skill['name']}.py"
        
        if not py_file.exists():
            return False, "Python file not found", 0.0
        
        start_time = time.time()
        
        try:
            # Импортируем и тестируем
            spec = __import__("importlib.util").util.spec_from_file_location(
                skill["name"], py_file
            )
            module = __import__("importlib.util").util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Ищем класс
            class_name = skill["name"].replace("-", "").replace("_", "").title() + "Skill"
            skill_class = None
            
            for name, obj in module.__dict__.items():
                if isinstance(obj, type) and "Skill" in name:
                    skill_class = obj
                    break
            
            if not skill_class:
                return False, "Skill class not found", 0.0
            
            # Создаем инстанс и тестируем
            instance = skill_class()
            
            # Проверяем validate
            if hasattr(instance, "validate"):
                is_valid = instance.validate()
            else:
                is_valid = True
            
            # Проверяем process
            if hasattr(instance, "process"):
                result = instance.process({"action": "test"})
                if isinstance(result, dict) and "status" in result:
                    elapsed = time.time() - start_time
                    return is_valid, f"Functional OK (status={result['status']})", elapsed
                else:
                    return False, "process() returned invalid format", 0.0
            else:
                return False, "process() method not found", 0.0
                
        except Exception as e:
            elapsed = time.time() - start_time
            return False, f"Functional Error: {str(e)[:100]}", elapsed
    
    def calculate_fitness(self, results: Dict) -> float:
        """Вычисляет итоговый fitness_score (0.0 - 1.0)"""
        weights = {
            "syntax": 0.3,
            "import": 0.3,
            "functional": 0.4
        }
        
        score = 0.0
        
        if results["syntax"]["passed"]:
            score += weights["syntax"]
        
        if results["import"]["passed"]:
            score += weights["import"]
        
        if results["functional"]["passed"]:
            score += weights["functional"]
        
        # Бонус за скорость
        if results["functional"]["time_ms"] < 100:
            score = min(1.0, score + 0.1)
        
        return round(score, 2)
    
    def test_skill(self, skill_file: Path) -> Dict:
        """Полное тестирование одного скилла"""
        skill = self.load_skill(skill_file)
        skill_name = skill.get("name", "unknown")
        
        print(f"🧪 Тестирование: {skill_name}")
        
        results = {
            "skill_name": skill_name,
            "skill_id": skill.get("skill_id", "unknown"),
            "tested_at": datetime.now().isoformat(),
            "syntax": {},
            "import": {},
            "functional": {}
        }
        
        # Тест 1: Синтаксис
        passed, message = self.run_syntax_test(skill)
        results["syntax"] = {"passed": passed, "message": message}
        print(f"   Syntax: {'✅' if passed else '❌'} {message}")
        
        # Тест 2: Импорт
        passed, message = self.run_import_test(skill)
        results["import"] = {"passed": passed, "message": message}
        print(f"   Import: {'✅' if passed else '❌'} {message}")
        
        # Тест 3: Функционал
        passed, message, elapsed = self.run_functional_test(skill)
        results["functional"] = {
            "passed": passed,
            "message": message,
            "time_ms": round(elapsed * 1000, 2)
        }
        print(f"   Functional: {'✅' if passed else '❌'} {message} ({elapsed*1000:.1f}ms)")
        
        # Вычисляем fitness
        fitness = self.calculate_fitness(results)
        results["fitness_score"] = fitness
        print(f"   Fitness Score: {fitness}")
        
        return results
    
    def update_skill_status(self, skill_file: Path, test_results: Dict):
        """Обновляет статус скилла и перемещает между директориями"""
        skill = self.load_skill(skill_file)
        fitness = test_results["fitness_score"]
        
        # Обновляем genome
        if "genome" not in skill:
            skill["genome"] = {}
        
        skill["genome"]["fitness_score"] = fitness
        skill["genome"]["last_evaluated"] = datetime.now().isoformat()
        skill["genome"]["test_results"] = {
            "syntax": test_results["syntax"],
            "import": test_results["import"],
            "functional": test_results["functional"]
        }
        
        # Определяем статус
        if fitness >= 0.7:
            skill["status"] = "tested"
            new_dir = self.tested_dir
            print(f"   ➡️  Moved to tested/ (fitness={fitness})")
        elif fitness >= 0.3:
            skill["status"] = "generated"  # Остается, можно доработать
            new_dir = self.generated_dir
            print(f"   ➡️  Stay in generated/ (fitness={fitness}, needs improvement)")
        else:
            skill["status"] = "retired"
            skill["retired_reason"] = f"Low fitness score: {fitness}"
            new_dir = self.retired_dir
            print(f"   ➡️  Moved to retired/ (fitness={fitness})")
        
        # Сохраняем обновленный YAML
        new_path = new_dir / skill_file.name
        self.save_skill(skill, new_path)
        
        # Удаляем из старой директории, если переместили
        if new_dir != self.generated_dir:
            skill_file.unlink()
            py_file = self.generated_dir / f"{skill['name']}.py"
            if py_file.exists():
                py_file.unlink()
        
        return new_path
    
    def run_all_tests(self) -> List[Dict]:
        """Тестирует все скиллы в generated/"""
        all_results = []
        
        skill_files = list(self.generated_dir.glob("*.yaml"))
        
        if not skill_files:
            print("⚠️ Нет скиллов для тестирования в generated/")
            return []
        
        print(f"🔬 Тестирование {len(skill_files)} скиллов...")
        print("=" * 50)
        
        for skill_file in skill_files:
            results = self.test_skill(skill_file)
            all_results.append(results)
            
            # Обновляем статус
            self.update_skill_status(skill_file, results)
            print()
        
        # Сохраняем итоговый отчет
        report_file = self.results_dir / f"test-run-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump({
                "run_date": datetime.now().isoformat(),
                "total_skills": len(all_results),
                "passed": len([r for r in all_results if r["fitness_score"] >= 0.7]),
                "failed": len([r for r in all_results if r["fitness_score"] < 0.3]),
                "needs_work": len([r for r in all_results if 0.3 <= r["fitness_score"] < 0.7]),
                "results": all_results
            }, f, indent=2, ensure_ascii=False)
        
        print(f"📊 Отчет сохранен: {report_file}")
        return all_results

if __name__ == "__main__":
    tester = SkillTester()
    results = tester.run_all_tests()
    
    print("\n" + "=" * 50)
    print("🏁 Итоги тестирования:")
    print(f"   Всего: {len(results)}")
    print(f"   Успешно (fitness>=0.7): {len([r for r in results if r['fitness_score'] >= 0.7])}")
    print(f"   Требует доработки: {len([r for r in results if 0.3 <= r['fitness_score'] < 0.7])}")
    print(f"   Отклонено: {len([r for r in results if r['fitness_score'] < 0.3])}")
