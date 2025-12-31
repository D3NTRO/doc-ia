# utils/pdf_exporter.py

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER
from datetime import datetime
import io

class ConversationPDFExporter:
    """Exporta conversaciones de Doc.ia a PDF"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Crea estilos personalizados"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor='#1E88E5',
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        
        self.styles.add(ParagraphStyle(
            name='UserQuestion',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor='#424242',
            spaceAfter=10,
            leftIndent=20,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='DocResponse',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor='#212121',
            spaceAfter=20,
            leftIndent=20,
            rightIndent=20
        ))
        
        self.styles.add(ParagraphStyle(
            name='Metadata',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor='#757575',
            spaceAfter=5
        ))
    
    def export_conversation(
        self,
        questions: list,
        responses: list,
        user_level: str,
        mode: str,
        username: str = "Usuario"
    ) -> bytes:
        """Exporta conversación a PDF"""
        buffer = io.BytesIO()
        
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        story = []
        
        # Título
        story.append(Paragraph("🩺 Doc.ia - Conversación Médica", self.styles['CustomTitle']))
        story.append(Spacer(1, 0.2 * inch))
        
        # Metadatos
        metadata_text = f"""
        <b>Usuario:</b> {username}<br/>
        <b>Nivel:</b> {user_level}<br/>
        <b>Modo:</b> {mode}<br/>
        <b>Fecha:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}<br/>
        <b>Total intercambios:</b> {len(questions)}
        """
        story.append(Paragraph(metadata_text, self.styles['Metadata']))
        story.append(Spacer(1, 0.3 * inch))
        
        # Cada pregunta-respuesta
        for i, (question, response) in enumerate(zip(questions, responses), 1):
            story.append(Paragraph(
                f"<b>── Consulta {i} ──</b>",
                self.styles['Heading2']
            ))
            story.append(Spacer(1, 0.1 * inch))
            
            story.append(Paragraph(
                f"<b>Pregunta:</b> {self._clean_text(question)}",
                self.styles['UserQuestion']
            ))
            
            story.append(Paragraph(
                f"<b>Respuesta:</b>",
                self.styles['Normal']
            ))
            story.append(Paragraph(
                self._clean_text(response),
                self.styles['DocResponse']
            ))
            
            story.append(Spacer(1, 0.3 * inch))
        
        # Footer
        footer_text = "<i>Doc.ia v1.0 | Asistente educativo - No sustituye evaluación médica profesional</i>"
        story.append(Paragraph(footer_text, self.styles['Metadata']))
        
        doc.build(story)
        
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes
    
    def _clean_text(self, text: str) -> str:
        """Limpia texto para PDF"""
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        return text