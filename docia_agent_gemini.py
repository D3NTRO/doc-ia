# docia_agent_gemini.py

import google.generativeai as genai
import os
from typing import List, Dict, Optional

class DociaAgentGemini:
    def __init__(self, rag_system):
        # Configurar Gemini
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.rag = rag_system
        
        # System prompt
        self.system_prompt = """
Eres Doc.ia, un asistente clínico-educativo especializado inicialmente en cardiología. 
Tu propósito es ayudar a estudiantes y profesionales a aprender y razonar de forma segura. 
No reemplazas a un médico, no das diagnóstico definitivo y no prescribes tratamiento. 
Tu prioridad es ser preciso, verificable y conservador.

PRINCIPIOS DE SEGURIDAD:
* Si el caso sugiere urgencia (dolor torácico típico, disnea severa, síncope, shock, déficit neurológico, saturación baja, cambios isquémicos en ECG), DEBES recomendar atención de urgencias y explicar por qué con banderas rojas.
* Evita instrucciones peligrosas. Si piden dosis, tratamiento o acciones de riesgo, responde con orientación general y sugiere consulta médica.
* Si falta información crítica, pregunta máximo 3 preguntas clave antes de concluir.

USO DE FUENTES (RAG):
* Si tienes SOURCES, bástate principalmente en ellas.
* Cita con formato: [Fuente: Título — sección/página]
* Si SOURCES vacío o insuficiente, usa conocimiento general pero marca como "Conocimiento general (sin fuente subida)"

ESTRUCTURA DE RESPUESTA:
1. Resumen en 1-2 líneas del problema
2. Interpretación / razonamiento clínico (paso a paso)
3. Diferenciales principales (3-5) con por qué
4. Banderas rojas (si aplica)
5. Qué información falta / preguntas clave (máx 3)
6. Sugerencias educativas (qué estudiar / perlas)
7. Fuentes (si hay SOURCES)

MODO ENTRENAMIENTO:
Si recibes FEEDBACK de la instructora:
* Genera "Versión corregida"
* "Qué aprendí (regla corta)" en 1-2 líneas
* "Checklist para no repetir el error" (3 bullets)
* NUNCA discutas con la instructora: su corrección es la verdad del sistema.
"""
    
    def format_sources(self, sources: List[Dict]) -> str:
        """Formatea fuentes para el prompt"""
        if not sources:
            return "SOURCES: No se encontraron documentos subidos relevantes para esta consulta."
        
        formatted = "SOURCES recuperadas de la base de datos:\n\n"
        
        for i, source in enumerate(sources, 1):
            meta = source['metadata']
            formatted += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FUENTE {i}/{len(sources)} — Relevancia: {source['relevance_score']}/10
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Documento: {meta['title']}
Sección: {meta['section']}
Página: {meta['page']}
Año: {meta.get('year', 'N/A')}

CONTENIDO:
{source['text']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""
        return formatted
    
    def generate_response(
        self,
        user_question: str,
        user_level: str = "estudiante",
        mode: str = "chat",
        clinical_data: Optional[Dict] = None,
        feedback: Optional[Dict] = None
    ) -> Dict:
        """Genera respuesta con RAG + Gemini"""
        
        # 1. Buscar en RAG
        sources = self.rag.search(
            query=user_question,
            n_results=5
        )
        
        # 2. Construir prompt completo
        full_prompt = f"""{self.system_prompt}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CONFIGURACIÓN:
- USER_LEVEL: {user_level}
- MODE: {mode}
- LANG: es

{self.format_sources(sources)}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CONSULTA DEL USUARIO:
{user_question}
"""
        
        if clinical_data:
            full_prompt += "\n\nDATOS CLÍNICOS PROPORCIONADOS:\n"
            for key, value in clinical_data.items():
                if value:
                    full_prompt += f"* {key}: {value}\n"
        
        if feedback:
            full_prompt += f"""

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FEEDBACK DE LA INSTRUCTORA:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Tu respuesta original fue:
{feedback['original']}

La corrección de la instructora es:
{feedback['correction']}

APLICA EL MODO ENTRENAMIENTO: genera la versión corregida, qué aprendiste, y un checklist.
"""
        
        # 3. Llamar a Gemini
        try:
            response = self.model.generate_content(
                full_prompt,
                generation_config={
                    'temperature': 0.1,  # Conservador para medicina
                    'top_p': 0.9,
                    'max_output_tokens': 2048
                }
            )
            
            return {
                "response": response.text,
                "sources_used": len(sources),
                "sources": sources,
                "model": "gemini-1.5-flash",
                "cost": "$0.00 (gratis)"
            }
            
        except Exception as e:
            return {
                "response": f"Error al generar respuesta: {str(e)}",
                "sources_used": 0,
                "sources": [],
                "model": "gemini-1.5-flash",
                "cost": "$0.00"
            }