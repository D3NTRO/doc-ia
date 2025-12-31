# 🩺 Doc.ia

Asistente clínico-educativo con sistema RAG especializado en cardiología.

## 🚀 Características

- ✅ Sistema RAG con Chroma DB
- ✅ Procesamiento de PDFs y PPTs médicos
- ✅ Embeddings locales gratuitos
- ✅ Integración con Gemini 2.5 Flash
- ✅ Modo instructora con feedback
- ✅ Sistema multi-usuario
- ✅ Exportación de conversaciones a PDF
- ✅ Historial de correcciones
- ✅ Upload de imágenes ECG
- ✅ 100% gratis (solo API key de Google)

## 📦 Instalación

### 1. Clonar repositorio
```bash
git clone https://github.com/D3NTRO/doc-ia.git
cd doc-ia
```

### 2. Crear entorno virtual
```bash
python -m venv docia_env
docia_env\Scripts\activate  # Windows
source docia_env/bin/activate  # Mac/Linux
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar API Key
- Obtener key gratuita en: https://aistudio.google.com/app/apikey
- Crear archivo `.env`:
```
GOOGLE_API_KEY="tu_key_aqui"
```

### 5. Ejecutar
```bash
streamlit run app.py
```

## 🌐 Deployment

La app está deployada en: https://doct-ia.streamlit.app

## 👥 Uso

### Modo Chat
1. Selecciona tu usuario
2. Sube documentos médicos (PDFs/PPTs)
3. Haz consultas médicas
4. Doc.ia responde basándose en TUS documentos

### Modo ECG
1. Sube imagen del ECG
2. Describe hallazgos en texto
3. Doc.ia analiza en 6 pasos sistemáticos

### Modo Instructora
1. Activa "Modo instructora"
2. Evalúa respuestas (correcta/mejorable/incorrecta)
3. Proporciona correcciones
4. Doc.ia aprende y mejora

## 📊 Tecnologías

- **Frontend:** Streamlit
- **LLM:** Google Gemini 2.5 Flash
- **Vector DB:** Chroma
- **Embeddings:** Sentence Transformers (all-mpnet-base-v2)
- **PDF Processing:** PyMuPDF, ReportLab
- **PPT Processing:** python-pptx

## 👨‍💻 Equipo

- **Desarrollador:** Denis
- **Instructora médica:** Dianik

## 📄 Licencia

Proyecto educativo - Uso académico

---

**⚠️ Disclaimer:** Doc.ia es un asistente educativo y NO sustituye la evaluación médica profesional.