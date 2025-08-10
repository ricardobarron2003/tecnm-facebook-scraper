import os
import numpy as np
from datetime import datetime
from sklearn.metrics.pairwise import cosine_similarity
import warnings
import logging

warnings.filterwarnings('ignore')

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración optimizada
PUBLICACIONES_FILE = os.path.join(os.path.dirname(__file__), "publicaciones_tec.txt")
UPDATE_INTERVAL = 3600  # 1 hora en segundos
MAX_PUBLICATIONS = 50   # Límite de publicaciones a procesar

class ChatbotTecNM:
    def __init__(self):
        logger.info("Inicializando ChatbotTecNM...")
        self.model = self.load_model()
        self.publicaciones = []
        self.embeddings = None
        self.last_update = None
        self.load_publications()
        logger.info("ChatbotTecNM inicializado correctamente")
    
    def load_model(self):
        """Carga un modelo optimizado con manejo de errores"""
        logger.info("Cargando modelo de embeddings...")
        try:
            from sentence_transformers import SentenceTransformer
            # Modelo más ligero para producción
            model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2', device='cpu')
            logger.info("Modelo cargado exitosamente")
            return model
        except Exception as e:
            logger.error(f"Error cargando modelo: {str(e)}")
            raise
    
    def load_publications(self):
        """Carga optimizada de publicaciones"""
        logger.info(f"Intentando cargar publicaciones desde: {PUBLICACIONES_FILE}")
        try:
            if not os.path.exists(PUBLICACIONES_FILE):
                logger.error(f"Archivo no encontrado: {PUBLICACIONES_FILE}")
                raise FileNotFoundError(f"Archivo de publicaciones no encontrado: {PUBLICACIONES_FILE}")
            
            with open(PUBLICACIONES_FILE, 'r', encoding='utf-8') as f:
                self.publicaciones = [line.strip() for line in f if line.strip()][-MAX_PUBLICATIONS:]
            
            if not self.publicaciones:
                logger.warning("Archivo de publicaciones está vacío")
                return
            
            logger.info(f"Cargadas {len(self.publicaciones)} publicaciones")
            
            # Procesar en lotes para ahorrar memoria
            batch_size = 10
            embeddings = []
            for i in range(0, len(self.publicaciones), batch_size):
                batch = self.publicaciones[i:i+batch_size]
                logger.debug(f"Procesando lote {i//batch_size + 1}/{(len(self.publicaciones)-1)//batch_size + 1}")
                embeddings.append(self.model.encode(batch))
            
            self.embeddings = np.concatenate(embeddings)
            self.last_update = datetime.now()
            logger.info("Embeddings de publicaciones generados exitosamente")
            
        except Exception as e:
            logger.error(f"Error cargando publicaciones: {str(e)}")
            raise
    
    def get_top_publications(self, query, top_k=2):
        """Obtiene las publicaciones más relevantes"""
        try:
            query_embedding = self.model.encode([query])
            similarities = cosine_similarity(query_embedding, self.embeddings)[0]
            
            # Obtener los índices de las top_k publicaciones más relevantes
            top_indices = np.argsort(similarities)[-top_k:][::-1]
            return [(self.publicaciones[i], similarities[i]) for i in top_indices]
        except Exception as e:
            logger.error(f"Error buscando publicaciones: {str(e)}")
            return []
    
    def generate_response(self, query):
        """Genera respuesta con la publicación principal y una sugerencia"""
        try:
            logger.info(f"Generando respuesta para: '{query}'")
            
            if not self.publicaciones:
                return "No hay publicaciones disponibles. Por favor intenta más tarde."
            
            top_pubs = self.get_top_publications(query)
            
            if not top_pubs or top_pubs[0][1] < 0.2:  # Umbral mínimo de relevancia
                return "No encontré información relevante sobre ese tema."
            
            response = []
            # Primera publicación (la más relevante)
            main_pub, main_score = top_pubs[0]
            response.append(f"🔍 Este es el resultado más relevante (confianza: {main_score:.2f}):")
            response.append(main_pub)
            
            # Segunda publicación como sugerencia (si tiene suficiente relevancia)
            if len(top_pubs) > 1 and top_pubs[1][1] > 0.15:
                sug_pub, sug_score = top_pubs[1]
                response.append("")
                response.append(f"💡 También te podría interesar (confianza: {sug_score:.2f}):")
                response.append(sug_pub)
            
            return "\n\n".join(response)
            
        except Exception as e:
            logger.error(f"Error generando respuesta: {str(e)}")
            return "Disculpa, ocurrió un error al procesar tu solicitud."