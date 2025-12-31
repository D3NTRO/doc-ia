# rag_system.py

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional
from datetime import datetime
import os

class DociaRAG:
    def __init__(self, persist_directory="./chroma_db"):
        """
        Sistema RAG para Doc.ia
        - persist_directory: donde se guardan los documentos indexados
        """
        print("🔄 Inicializando sistema RAG...")
        
        # Inicializar Chroma (base de datos vectorial)
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Modelo de embeddings local (GRATIS - corre en tu PC)
        print("🔄 Cargando modelo de embeddings (puede tardar 1-2 min la primera vez)...")
        self.embedding_model = SentenceTransformer('all-mpnet-base-v2')
        print("✅ Modelo de embeddings cargado")
        
        # Crear o cargar colección
        try:
            self.collection = self.client.get_collection("docia_medical_docs")
            print(f"✅ Colección existente cargada ({self.collection.count()} chunks)")
        except:
            self.collection = self.client.create_collection(
                name="docia_medical_docs",
                metadata={"description": "Documentación médica de Doc.ia"}
            )
            print("✅ Nueva colección creada")
    
    def add_document(self, doc_data: Dict, metadata: Dict, uploaded_by: str = "sistema") -> str:
        """
        Añade un documento completo a la base vectorial
        
        Args:
            doc_data: dict con 'chunks' del DocumentProcessor
            metadata: dict con title, type, year, specialty, etc.
            uploaded_by: nombre del usuario que sube el documento
        
        Returns:
            doc_id: identificador único del documento
        """
        chunks = doc_data['chunks']
        
        # Generar ID único para el documento
        safe_title = metadata['title'][:30].replace(' ', '_').replace('/', '_')
        doc_id = f"{metadata.get('specialty', 'general')}_{safe_title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        texts = []
        metadatas = []
        ids = []
        
        print(f"📝 Preparando {len(chunks)} chunks para indexar...")
        
        for i, chunk in enumerate(chunks):
            chunk_id = f"{doc_id}_chunk_{i:04d}"
            
            texts.append(chunk['text'])
            
            metadatas.append({
                "doc_id": doc_id,
                "title": metadata['title'],
                "type": metadata.get('type', 'guideline'),
                "specialty": metadata.get('specialty', 'cardiologia'),
                "year": str(metadata.get('year', 2024)),
                "page": str(chunk.get('page', 0)),
                "section": chunk.get('section', 'Sin sección'),
                "tokens": str(chunk.get('tokens', 0)),
                "upload_date": datetime.now().isoformat(),
                "uploaded_by": uploaded_by  # NUEVO: quién subió el documento
            })
            
            ids.append(chunk_id)
        
        # Generar embeddings (vectores numéricos)
        print(f"🔄 Generando embeddings para {len(texts)} chunks...")
        embeddings = self.embedding_model.encode(
            texts, 
            show_progress_bar=True,
            batch_size=32
        ).tolist()
        
        # Añadir a Chroma en batches de 100
        batch_size = 100
        print(f"💾 Guardando en base de datos...")
        
        for i in range(0, len(texts), batch_size):
            end_idx = min(i + batch_size, len(texts))
            
            self.collection.add(
                documents=texts[i:end_idx],
                embeddings=embeddings[i:end_idx],
                metadatas=metadatas[i:end_idx],
                ids=ids[i:end_idx]
            )
            
            print(f"  ✓ Batch {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1}")
        
        print(f"✅ Documento '{metadata['title']}' añadido exitosamente")
        print(f"   📊 Total: {len(chunks)} chunks indexados")
        
        return doc_id
    
    def search(
        self, 
        query: str, 
        n_results: int = 5,
        filters: Optional[Dict] = None,
        user_id: Optional[str] = None  # NUEVO: filtrar por usuario
    ) -> List[Dict]:
        """
        Busca fragmentos relevantes en la base de datos
        
        Args:
            query: pregunta del usuario
            n_results: cuántos resultados devolver (máx)
            filters: dict con filtros, ej: {"specialty": "cardiologia"}
            user_id: filtrar solo documentos de este usuario (None = todos)
        
        Returns:
            Lista de diccionarios con los chunks más relevantes
        """
        # Generar embedding de la query
        query_embedding = self.embedding_model.encode(query).tolist()
        
        # Construir filtros
        where_filter = filters.copy() if filters else {}
        
        # Agregar filtro de usuario si se proporciona
        if user_id:
            where_filter["uploaded_by"] = user_id
        
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where_filter if where_filter else None
            )
        except Exception as e:
            print(f"⚠️ Error en búsqueda: {e}")
            return []
        
        # Formatear resultados
        formatted = []
        
        if results['ids'] and len(results['ids'][0]) > 0:
            for i in range(len(results['ids'][0])):
                formatted.append({
                    "chunk_id": results['ids'][0][i],
                    "text": results['documents'][0][i],
                    "distance": results['distances'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "relevance_score": self._distance_to_score(results['distances'][0][i])
                })
        
        return formatted
    
    def _distance_to_score(self, distance: float) -> int:
        """
        Convierte distancia coseno a score 1-10
        Menor distancia = más similar = score alto
        """
        if distance < 0.4:
            return 10
        elif distance < 0.6:
            return 8
        elif distance < 0.8:
            return 6
        elif distance < 1.0:
            return 4
        else:
            return 2
    
    def get_collection_stats(self, user_id: Optional[str] = None) -> Dict:
        """
        Estadísticas de la colección
        
        Args:
            user_id: si se proporciona, solo stats de ese usuario
        """
        count = self.collection.count()
        
        if count == 0:
            return {
                "total_chunks": 0,
                "unique_docs": 0,
                "by_user": {}
            }
        
        try:
            all_metadata = self.collection.get()['metadatas']
            
            # Si hay filtro de usuario
            if user_id:
                user_metadata = [m for m in all_metadata if m.get('uploaded_by') == user_id]
                unique_docs = set([m.get('doc_id', 'unknown') for m in user_metadata])
                
                return {
                    "total_chunks": len(user_metadata),
                    "unique_docs": len(unique_docs)
                }
            
            # Stats generales
            unique_docs = set([m.get('doc_id', 'unknown') for m in all_metadata])
            
            # Contar por usuario
            by_user = {}
            for m in all_metadata:
                user = m.get('uploaded_by', 'sistema')
                by_user[user] = by_user.get(user, 0) + 1
            
            return {
                "total_chunks": count,
                "unique_docs": len(unique_docs),
                "by_user": by_user
            }
            
        except Exception as e:
            print(f"⚠️ Error obteniendo stats: {e}")
            return {
                "total_chunks": count,
                "unique_docs": 0,
                "by_user": {}
            }
    
    def delete_document(self, doc_id: str) -> bool:
        """Elimina un documento completo"""
        try:
            # Buscar todos los chunks de ese documento
            results = self.collection.get(
                where={"doc_id": doc_id}
            )
            
            if results['ids']:
                self.collection.delete(ids=results['ids'])
                print(f"🗑️ Documento {doc_id} eliminado ({len(results['ids'])} chunks)")
                return True
            else:
                print(f"⚠️ No se encontró documento {doc_id}")
                return False
                
        except Exception as e:
            print(f"❌ Error al eliminar: {e}")
            return False
    
    def get_user_documents(self, user_id: str) -> List[Dict]:
        """
        Obtiene lista de documentos únicos de un usuario
        
        Returns:
            Lista de diccionarios con info de cada documento
        """
        try:
            results = self.collection.get(
                where={"uploaded_by": user_id}
            )
            
            if not results['metadatas']:
                return []
            
            # Agrupar por doc_id
            docs = {}
            for meta in results['metadatas']:
                doc_id = meta.get('doc_id')
                if doc_id and doc_id not in docs:
                    docs[doc_id] = {
                        'doc_id': doc_id,
                        'title': meta.get('title', 'Sin título'),
                        'type': meta.get('type', 'desconocido'),
                        'specialty': meta.get('specialty', 'general'),
                        'year': meta.get('year', 'N/A'),
                        'upload_date': meta.get('upload_date', 'N/A')
                    }
            
            return list(docs.values())
            
        except Exception as e:
            print(f"⚠️ Error obteniendo documentos de usuario: {e}")
            return []