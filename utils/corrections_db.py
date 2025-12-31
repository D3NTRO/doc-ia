# utils/corrections_db.py

import json
import os
from datetime import datetime
from typing import List, Dict

class CorrectionsDatabase:
    """Base de datos simple para historial de correcciones"""
    
    def __init__(self, db_path: str = "./corrections.json"):
        self.db_path = db_path
        self._ensure_db_exists()
    
    def _ensure_db_exists(self):
        """Crea archivo JSON si no existe"""
        if not os.path.exists(self.db_path):
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump({"corrections": []}, f, ensure_ascii=False, indent=2)
    
    def add_correction(
        self,
        user_question: str,
        original_response: str,
        correction: str,
        instructor: str = "Dianik",
        user_level: str = "estudiante",
        feedback_type: str = "incorrecta"
    ) -> bool:
        """Añade corrección al historial"""
        try:
            with open(self.db_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            new_correction = {
                "id": len(data["corrections"]) + 1,
                "timestamp": datetime.now().isoformat(),
                "instructor": instructor,
                "user_level": user_level,
                "feedback_type": feedback_type,
                "question": user_question,
                "original_response": original_response,
                "correction": correction
            }
            
            data["corrections"].append(new_correction)
            
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error guardando corrección: {e}")
            return False
    
    def get_all_corrections(self) -> List[Dict]:
        """Obtiene todas las correcciones"""
        try:
            with open(self.db_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data["corrections"]
        except:
            return []
    
    def get_recent_corrections(self, n: int = 10) -> List[Dict]:
        """Obtiene N correcciones más recientes"""
        all_corrections = self.get_all_corrections()
        return sorted(all_corrections, key=lambda x: x["timestamp"], reverse=True)[:n]
    
    def get_stats(self) -> Dict:
        """Estadísticas del historial"""
        corrections = self.get_all_corrections()
        
        if not corrections:
            return {
                "total": 0,
                "by_type": {},
                "by_instructor": {}
            }
        
        by_type = {}
        by_instructor = {}
        
        for c in corrections:
            feedback_type = c.get("feedback_type", "desconocido")
            by_type[feedback_type] = by_type.get(feedback_type, 0) + 1
            
            instructor = c.get("instructor", "desconocido")
            by_instructor[instructor] = by_instructor.get(instructor, 0) + 1
        
        return {
            "total": len(corrections),
            "by_type": by_type,
            "by_instructor": by_instructor
        }