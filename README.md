# 🩺 Doc.ia

Asistente clínico-educativo especializado en cardiología con sistema RAG.

## 🚀 Instalación

1. Clonar repositorio:
```bash
git clone https://github.com/tu-usuario/doc-ia.git
cd doc-ia
```

2. Crear entorno virtual:
```bash
python -m venv docia_env
docia_env\Scripts\activate  # Windows
source docia_env/bin/activate  # Mac/Linux
```

3. Instalar dependencias:
```bash
pip install streamlit google-generativeai python-dotenv chromadb sentence-transformers PyMuPDF python-pptx tiktoken
```

4. Configurar API Key:
- Obtener key gratuita en: https://aistudio.google.com/app/apikey
- Crear archivo `.env`:
```
GOOGLE_API_KEY=tu_key_aqui
```

5. Ejecutar:
```bash
streamlit run app.py
```

## 📚 Características

- ✅ Sistema RAG con Chroma DB
- ✅ Procesamiento de PDFs y PPTs médicos
- ✅ Embeddings locales gratuitos
- ✅ Integración con Gemini Flash
- ✅ Modo instructora para feedback
- ✅ 100% gratis (solo necesitas Google API Key)

## 👥 Equipo

- **Desarrollador:** Denis
- **Instructora médica:** Dianik

## 📄 Licencia

Proyecto educativo - Uso académico