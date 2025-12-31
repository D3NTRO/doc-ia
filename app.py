# app.py

import streamlit as st
import os
from dotenv import load_dotenv
from rag_system import DociaRAG
from docia_agent_gemini import DociaAgentGemini
from document_processor import DocumentProcessor
from datetime import datetime
from PIL import Image
import io

# Intentar importar utilidades (si existen)
try:
    from utils.pdf_exporter import ConversationPDFExporter
    from utils.corrections_db import CorrectionsDatabase
    PDF_EXPORT_AVAILABLE = True
except ImportError:
    PDF_EXPORT_AVAILABLE = False
    print("⚠️ Utilidades de exportación no disponibles")

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
    
    # Inicializar DB de correcciones si está disponible
    corrections_db = None
    if PDF_EXPORT_AVAILABLE:
        try:
            corrections_db = CorrectionsDatabase()
        except:
            pass
    
    return rag, agent, processor, corrections_db

rag, agent, processor, corrections_db = init_system()

# Inicializar session state
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = {
        'questions': [],
        'responses': []
    }

if 'current_user' not in st.session_state:
    st.session_state.current_user = "Dianik"

if 'uploaded_ecg_image' not in st.session_state:
    st.session_state.uploaded_ecg_image = None

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
    .user-badge {
        background-color: #E3F2FD;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
        color: #1976D2;
        text-align: center;
        margin-bottom: 1rem;
    }
    .info-box {
        background-color: #E8F5E9;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #4CAF50;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="main-header">🩺 Doc.ia</h1>', unsafe_allow_html=True)
st.markdown("**Asistente clínico-educativo especializado en cardiología**")

# Sidebar - Panel de control
with st.sidebar:
    # Selector de usuario
    st.header("👤 Usuario")
    
    available_users = ["Dianik", "Denis", "Estudiante 1", "Estudiante 2", "Nuevo usuario..."]
    
    selected_user = st.selectbox(
        "¿Quién eres?",
        available_users,
        index=available_users.index(st.session_state.current_user) if st.session_state.current_user in available_users else 0
    )
    
    if selected_user == "Nuevo usuario...":
        new_user = st.text_input("Nombre del nuevo usuario:")
        if new_user and st.button("Crear usuario"):
            st.session_state.current_user = new_user
            st.success(f"✅ Usuario '{new_user}' creado")
            st.rerun()
    else:
        if selected_user != st.session_state.current_user:
            st.session_state.current_user = selected_user
            st.rerun()
    
    st.markdown(f'<div class="user-badge">👋 Hola, {st.session_state.current_user}</div>', unsafe_allow_html=True)
    
    st.divider()
    
    # Configuración
    st.header("⚙️ Configuración")
    
    user_level = st.selectbox(
        "Nivel del usuario",
        ["estudiante", "interno", "residente"],
        index=0
    )
    
    mode = st.selectbox(
        "Modo",
        ["chat", "ecg"],
        index=0,
        help="Chat: consultas normales | ECG: análisis de electrocardiogramas"
    )
    
    # Filtro de búsqueda
    search_scope = st.radio(
        "Buscar en:",
        ["Todos los documentos", "Solo mis documentos"],
        index=0,
        help="Limitar búsqueda a documentos que tú subiste"
    )
    
    st.divider()
    
    # NUEVO: Sección "Sobre Doc.ia"
    with st.expander("ℹ️ Sobre Doc.ia", expanded=False):
        st.markdown("""
        **Doc.ia** es tu asistente clínico-educativo especializado en cardiología.
        
        **¿Qué puedo hacer?**
        - 🔍 Responder consultas médicas basándome en documentos subidos
        - 📊 Analizar ECGs (describe el ECG en texto)
        - 📚 Buscar información en guías y libros que suban
        - 🧠 Aprender de las correcciones de la instructora
        
        **¿Cómo funciono?**
        - Uso un sistema RAG (Retrieval Augmented Generation)
        - Busco en los documentos que suben para darte respuestas precisas
        - Cito las fuentes de donde saqué la información
        - Cuando no hay documentos, uso mi conocimiento general (pero te lo digo)
        
        **Modos disponibles:**
        - **CHAT**: Consultas clínicas normales
        - **ECG**: Análisis sistemático en 6 pasos
        
        **Creado por:** Denis  
        **Para:** Dianik y estudiantes de cardiología  
        **Versión:** 1.0
        """)
    
    st.divider()
    
    # Panel Instructora
    st.header("👩‍⚕️ Panel Instructora")
    
    is_instructor = st.checkbox(
        "Modo instructora", 
        value=(st.session_state.current_user == "Dianik")
    )
    
    if is_instructor:
        st.info("🔓 Modo entrenamiento activado")
        
        # Mostrar historial de correcciones
        if corrections_db and st.button("📋 Ver historial de correcciones"):
            stats = corrections_db.get_stats()
            st.metric("Total correcciones", stats['total'])
            
            if stats['total'] > 0:
                recent = corrections_db.get_recent_corrections(5)
                st.write("**Últimas 5 correcciones:**")
                for corr in recent:
                    with st.expander(f"{corr['timestamp'][:10]} - {corr['feedback_type']}"):
                        st.write(f"**Pregunta:** {corr['question'][:100]}...")
                        st.write(f"**Corrección:** {corr['correction'][:200]}...")
    
    st.divider()
    
    # Cargar documentos
    st.header("📚 Cargar documentos")
    
    uploaded_file = st.file_uploader(
        "Sube PDF o PPT",
        type=['pdf', 'pptx'],
        help="Documentos médicos (guías, papers, etc.)"
    )
    
    if uploaded_file:
        with st.spinner("📄 Procesando documento..."):
            temp_path = f"./temp_{uploaded_file.name}"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            try:
                if uploaded_file.name.endswith('.pdf'):
                    doc_data = processor.extract_from_pdf(temp_path)
                else:
                    doc_data = processor.extract_from_ppt(temp_path)
                
                st.subheader("Metadatos del documento")
                title = st.text_input("Título", value=doc_data['metadata'].get('title', ''))
                specialty = st.selectbox("Especialidad", ["cardiologia", "neumologia", "neurologia", "general"])
                year = st.number_input("Año", min_value=2000, max_value=2025, value=2024)
                doc_type = st.selectbox("Tipo", ["guideline", "textbook", "paper", "notes"])
                
                if st.button("💾 Guardar en base de datos"):
                    metadata = {
                        "title": title,
                        "specialty": specialty,
                        "year": year,
                        "type": doc_type
                    }
                    
                    # NUEVO: Guardar con usuario
                    doc_id = rag.add_document(
                        doc_data, 
                        metadata,
                        uploaded_by=st.session_state.current_user
                    )
                    
                    st.success(f"✅ Documento '{title}' cargado con éxito!")
                    st.info(f"📊 {len(doc_data['chunks'])} fragmentos indexados")
                    st.info(f"👤 Subido por: {st.session_state.current_user}")
                    
                    os.remove(temp_path)
                    st.rerun()
                    
            except Exception as e:
                st.error(f"❌ Error al procesar: {str(e)}")
                if os.path.exists(temp_path):
                    os.remove(temp_path)
    
    st.divider()
    
    # Estadísticas
    st.header("📊 Estadísticas")
    
    # Determinar user_id para stats
    stats_user_id = st.session_state.current_user if search_scope == "Solo mis documentos" else None
    stats = rag.get_collection_stats(user_id=stats_user_id)
    
    st.metric("Total chunks", stats['total_chunks'])
    st.metric("Documentos únicos", stats['unique_docs'])
    
    # Mostrar distribución por usuario (solo si es vista global)
    if search_scope == "Todos los documentos" and stats.get('by_user'):
        with st.expander("Por usuario"):
            for user, count in stats['by_user'].items():
                st.write(f"**{user}:** {count} chunks")
    
    # NUEVO: Mostrar mis documentos
    if st.button("📄 Ver mis documentos"):
        my_docs = rag.get_user_documents(st.session_state.current_user)
        if my_docs:
            st.write(f"**Tus documentos ({len(my_docs)}):**")
            for doc in my_docs:
                with st.expander(f"{doc['title']} ({doc['year']})"):
                    st.write(f"**Tipo:** {doc['type']}")
                    st.write(f"**Especialidad:** {doc['specialty']}")
                    st.write(f"**Fecha subida:** {doc['upload_date'][:10]}")
        else:
            st.info("No has subido documentos aún")

# Main chat area
st.header("💬 Consulta médica")

# NUEVO: Upload de imagen ECG (si modo = ecg)
if mode == "ecg":
    st.info("📸 Modo ECG: Sube una imagen del electrocardiograma")
    
    ecg_image = st.file_uploader(
        "Imagen del ECG",
        type=['png', 'jpg', 'jpeg'],
        help="Sube una foto clara del ECG"
    )
    
    if ecg_image:
        # Mostrar imagen
        image = Image.open(ecg_image)
        st.image(image, caption="ECG subido", use_container_width=True)
        st.session_state.uploaded_ecg_image = ecg_image
        st.success("✅ Imagen cargada. Describe los hallazgos del ECG en el campo de texto abajo.")

# Área de datos clínicos
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
    placeholder="Ej: ¿Cuáles son los criterios diagnósticos de IC con FEVI reducida?" if mode == "chat" else "Describe los hallazgos del ECG: Ritmo, FC, eje, intervalos, ST-T..."
)

# Botones de acción
col1, col2 = st.columns([3, 1])

with col1:
    consultar_btn = st.button("🔍 Consultar", type="primary")

with col2:
    if PDF_EXPORT_AVAILABLE and len(st.session_state.conversation_history['questions']) > 0:
        if st.button("📄 Exportar a PDF"):
            try:
                exporter = ConversationPDFExporter()
                pdf_bytes = exporter.export_conversation(
                    questions=st.session_state.conversation_history['questions'],
                    responses=st.session_state.conversation_history['responses'],
                    user_level=user_level,
                    mode=mode,
                    username=st.session_state.current_user
                )
                
                st.download_button(
                    label="💾 Descargar PDF",
                    data=pdf_bytes,
                    file_name=f"docia_conversacion_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    mime="application/pdf"
                )
                
            except Exception as e:
                st.error(f"Error al exportar: {str(e)}")

# Procesar consulta
if consultar_btn:
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
                # NUEVO: Determinar filtro de usuario
                user_filter = st.session_state.current_user if search_scope == "Solo mis documentos" else None
                
                # Modificar temporalmente el método search del agente
                original_search = agent.rag.search
                
                def filtered_search(query, n_results=5):
                    return original_search(query, n_results=n_results, user_id=user_filter)
                
                agent.rag.search = filtered_search
                
                result = agent.generate_response(
                    user_question=user_question,
                    user_level=user_level,
                    mode=mode,
                    clinical_data=clinical_data
                )
                
                # Restaurar método original
                agent.rag.search = original_search
                
                # Guardar en historial
                st.session_state.conversation_history['questions'].append(user_question)
                st.session_state.conversation_history['responses'].append(result['response'])
                
                # Mostrar respuesta
                st.markdown("### 🩺 Respuesta de Doc.ia")
                st.markdown(result['response'])
                
                # Mostrar fuentes
                if result['sources_used'] > 0:
                    with st.expander(f"📚 Fuentes consultadas ({result['sources_used']})", expanded=False):
                        for i, source in enumerate(result['sources'][:5], 1):
                            meta = source['metadata']
                            st.markdown(f"""
**Fuente {i}** - Relevancia: {source['relevance_score']}/10
- **Documento:** {meta['title']}
- **Sección:** {meta['section']}
- **Página:** {meta['page']}
- **Subido por:** {meta.get('uploaded_by', 'desconocido')}
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
                            height=150,
                            key="feedback_input"
                        )
                    with col2:
                        feedback_type = st.radio(
                            "Evaluación",
                            ["✅ Correcta", "⚠️ Mejorable", "❌ Incorrecta"],
                            key="feedback_type"
                        )
                    
                    if st.button("💾 Guardar feedback"):
                        # Guardar en BD de correcciones
                        if corrections_db and feedback_text:
                            corrections_db.add_correction(
                                user_question=user_question,
                                original_response=result['response'],
                                correction=feedback_text,
                                instructor=st.session_state.current_user,
                                user_level=user_level,
                                feedback_type=feedback_type.split()[1]  # Quitar emoji
                            )
                        
                        st.success("✅ Feedback guardado para entrenamiento")
                        
                        # Si es incorrecta, aplicar modo entrenamiento
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
st.markdown(f"""
<div style='text-align: center; color: gray;'>
    <small>Doc.ia v1.0 | Asistente educativo - No sustituye evaluación médica profesional</small><br/>
    <small>Usuario actual: {st.session_state.current_user} | Modelo: Gemini 2.5 Flash</small>
</div>
""", unsafe_allow_html=True)