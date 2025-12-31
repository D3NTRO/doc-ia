import streamlit as st
import os
from dotenv import load_dotenv
from rag_system import DociaRAG
from docia_agent_gemini import DociaAgentGemini
from document_processor import DocumentProcessor

# Configuración de página
st.set_page_config(
    page_title="Doc.ia - Asistente Médico",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Cargar variables de entorno
load_dotenv()

# Inicializar sistema (con cache para no recargar cada vez)
@st.cache_resource
def init_system():
    rag = DociaRAG(persist_directory="./chroma_db")
    agent = DociaAgentGemini(rag)
    processor = DocumentProcessor()
    return rag, agent, processor

rag, agent, processor = init_system()

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stButton>button {
        width: 100%;
        background-color: #1E88E5;
        color: white;
    }
    .feedback-section {
        background-color: #FFF3E0;
        padding: 1rem;
        border-radius: 10px;
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="main-header">🩺 Doc.ia</h1>', unsafe_allow_html=True)
st.markdown("**Asistente clínico-educativo especializado en cardiología**")

# Sidebar - Panel de control
with st.sidebar:
    st.header("⚙️ Configuración")
    
    # Nivel del usuario
    user_level = st.selectbox(
        "Nivel del usuario",
        ["estudiante", "interno", "residente"],
        index=0
    )
    
    # Modo
    mode = st.selectbox(
        "Modo",
        ["chat", "ecg", "quiz"],
        index=0
    )
    
    st.divider()
    
    # Sección de instructora
    st.header("👩‍⚕️ Panel Instructora")
    
    is_instructor = st.checkbox("Modo instructora", value=False)
    
    if is_instructor:
        st.info("🔓 Modo entrenamiento activado")
    
    st.divider()
    
    # Subir documentos
    st.header("📚 Cargar documentos")
    
    uploaded_file = st.file_uploader(
        "Sube PDF o PPT",
        type=['pdf', 'pptx'],
        help="Arrastra o selecciona guías médicas"
    )
    
    if uploaded_file:
        with st.spinner("📄 Procesando documento..."):
            # Guardar temporalmente
            temp_path = f"./temp_{uploaded_file.name}"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Procesar según tipo
            try:
                if uploaded_file.name.endswith('.pdf'):
                    doc_data = processor.extract_from_pdf(temp_path)
                else:
                    doc_data = processor.extract_from_ppt(temp_path)
                
                # Metadatos
                st.subheader("Metadatos del documento")
                title = st.text_input("Título", value=doc_data['metadata'].get('title', ''))
                specialty = st.selectbox("Especialidad", ["cardiologia", "neumologia", "neurologia"])
                year = st.number_input("Año", min_value=2000, max_value=2025, value=2024)
                doc_type = st.selectbox("Tipo", ["guideline", "textbook", "paper", "notes"])
                
                if st.button("💾 Guardar en base de datos"):
                    metadata = {
                        "title": title,
                        "specialty": specialty,
                        "year": year,
                        "type": doc_type
                    }
                    
                    doc_id = rag.add_document(doc_data, metadata)
                    st.success(f"✅ Documento '{title}' cargado con éxito!")
                    st.info(f"📊 {len(doc_data['chunks'])} fragmentos indexados")
                    
                    # Limpiar
                    os.remove(temp_path)
                    
            except Exception as e:
                st.error(f"❌ Error al procesar: {str(e)}")
    
    # Estadísticas
    st.divider()
    st.header("📊 Estadísticas")
    stats = rag.get_collection_stats()
    st.metric("Total chunks", stats['total_chunks'])
    st.metric("Documentos únicos", stats['unique_docs'])

# Main chat area
st.header("💬 Consulta médica")

# Área de datos clínicos (expandible)
with st.expander("📋 Datos clínicos (opcional)", expanded=False):
    col1, col2 = st.columns(2)
    
    with col1:
        edad_sexo = st.text_input("Edad/Sexo", placeholder="Ej: 65 años, masculino")
        sintomas = st.text_area("Síntomas", placeholder="Disnea de esfuerzo, ortopnea...")
        signos_vitales = st.text_input("Signos vitales", placeholder="TA, FC, FR, SatO2")
        
    with col2:
        antecedentes = st.text_area("Antecedentes", placeholder="HTA, DM2, tabaquismo...")
        medicacion = st.text_area("Medicación", placeholder="Enalapril, metformina...")
        hallazgos = st.text_area("Hallazgos", placeholder="ECG, labs, imágenes...")

# Input de consulta
user_question = st.text_area(
    "Escribe tu consulta médica:",
    height=100,
    placeholder="Ej: ¿Cuáles son los criterios diagnósticos de IC con FEVI reducida?"
)

# Botón de enviar
if st.button("🔍 Consultar", type="primary"):
    if not user_question:
        st.warning("⚠️ Por favor escribe una consulta")
    else:
        # Preparar datos clínicos
        clinical_data = {
            "Edad/sexo": edad_sexo,
            "Síntomas": sintomas,
            "Signos vitales": signos_vitales,
            "Antecedentes": antecedentes,
            "Medicación": medicacion,
            "Hallazgos": hallazgos
        } if any([edad_sexo, sintomas, signos_vitales, antecedentes, medicacion, hallazgos]) else None
        
        # Generar respuesta
        with st.spinner("🤔 Doc.ia está analizando..."):
            try:
                result = agent.generate_response(
                    user_question=user_question,
                    user_level=user_level,
                    mode=mode,
                    clinical_data=clinical_data
                )
                
                # Mostrar respuesta
                st.markdown("### 🩺 Respuesta de Doc.ia")
                st.markdown(result['response'])
                
                # Mostrar fuentes usadas
                if result['sources_used'] > 0:
                    with st.expander(f"📚 Fuentes consultadas ({result['sources_used']})", expanded=False):
                        for i, source in enumerate(result['sources'][:3], 1):
                            meta = source['metadata']
                            st.markdown(f"""
**Fuente {i}** - Relevancia: {source['relevance_score']}/10
- **Documento:** {meta['title']}
- **Sección:** {meta['section']}
- **Página:** {meta['page']}
                            """)
                
                # Modo instructora: feedback
                if is_instructor:
                    st.markdown("---")
                    st.markdown('<div class="feedback-section">', unsafe_allow_html=True)
                    st.markdown("### 👩‍⚕️ Feedback de Instructora")
                    
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        feedback_text = st.text_area(
                            "Corrección (si es necesaria):",
                            placeholder="Si la respuesta tiene errores, escribe aquí la versión correcta...",
                            height=150
                        )
                    with col2:
                        feedback_type = st.radio(
                            "Evaluación",
                            ["✅ Correcta", "⚠️ Mejorable", "❌ Incorrecta"]
                        )
                    
                    if st.button("💾 Guardar feedback"):
                        # Aquí guardarías el feedback en una BD
                        st.success("✅ Feedback guardado para entrenamiento")
                        
                        # Si hay corrección, aplicar modo entrenamiento
                        if feedback_text and feedback_type == "❌ Incorrecta":
                            with st.spinner("🧠 Aplicando modo entrenamiento..."):
                                training_result = agent.generate_response(
                                    user_question=user_question,
                                    user_level=user_level,
                                    mode=mode,
                                    clinical_data=clinical_data,
                                    feedback={
                                        'original': result['response'],
                                        'correction': feedback_text
                                    }
                                )
                                
                                st.markdown("### 📝 Versión corregida + Aprendizaje")
                                st.markdown(training_result['response'])
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.info("💡 Verifica que tu API key de Gemini esté configurada correctamente")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
    <small>Doc.ia v1.0 | Asistente educativo - No sustituye evaluación médica profesional</small>
</div>
""", unsafe_allow_html=True)