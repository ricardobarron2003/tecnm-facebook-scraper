
import subprocess
import time
from datetime import datetime
import os
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import warnings
warnings.filterwarnings('ignore')

SCRAPING_SCRIPT = os.path.join(os.path.dirname(__file__), "facebook_scrapping.py")
PUBLICACIONES_FILE = os.path.join(os.path.dirname(__file__), "publicaciones_tec.txt")
UPDATE_INTERVAL = 3600  # 1 hora en segundos
MODEL_NAME = 'paraphrase-TinyBERT-L6-v2'

class ChatbotTecNM:
    def __init__(self):
        self.model = None  # Carga diferida
        self.publicaciones = []
        self.embeddings = None  # Inicializado
        self.last_update = None  # Inicializado
        self.load_model()  # Cargar modelo al iniciar
        self.load_publications()  # Cargar publicaciones al iniciar
    
    def load_model(self):
        if self.model is None:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(MODEL_NAME)
    
    def run_scraping(self):
        """Ejecuta el script de scraping"""
        print(f"\n🔄 Ejecutando {SCRAPING_SCRIPT}...")
        try:
            result = subprocess.run(['python', SCRAPING_SCRIPT], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Scraping completado exitosamente")
                self.load_publications()
                return True
            else:
                print(f"❌ Error en scraping: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ Error al ejecutar scraping: {str(e)}")
            return False
    
    def load_publications(self):
        """Carga las publicaciones desde el archivo"""
        if not os.path.exists(PUBLICACIONES_FILE):
            print("⚠️ No se encontró el archivo de publicaciones")
            self.publicaciones = []
            self.embeddings = None
            return
        
        with open(PUBLICACIONES_FILE, 'r', encoding='utf-8') as f:
            self.publicaciones = [line.strip() for line in f if line.strip()]
        
        if self.publicaciones:
            print(f"📖 Cargadas {len(self.publicaciones)} publicaciones")
            # Precomputar embeddings para todas las publicaciones
            self.embeddings = self.model.encode(self.publicaciones)
        else:
            self.embeddings = None
        
        self.last_update = datetime.now()
    
    def check_for_updates(self):
        """Verifica si es tiempo de actualizar"""
        if not self.last_update or \
           (datetime.now() - self.last_update).total_seconds() > UPDATE_INTERVAL:
            self.run_scraping()
    
    def find_most_relevant(self, query, top_k=3):
        """Encuentra las publicaciones más relevantes a la consulta"""
        if not self.publicaciones or self.embeddings is None:
            return []
        
        # Calcular embedding para la consulta
        query_embedding = self.model.encode([query])
        
        # Calcular similitud coseno
        similarities = cosine_similarity(query_embedding, self.embeddings)[0]
        
        # Obtener los índices de las publicaciones más relevantes
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        return [(self.publicaciones[i], similarities[i]) for i in top_indices]
    
    def generate_response(self, query):
        """Genera una respuesta a la consulta del usuario"""
        self.check_for_updates()

        if not self.publicaciones or self.embeddings is None:
            return "No hay publicaciones disponibles. Por favor intenta más tarde."

        relevant_pubs = self.find_most_relevant(query, top_k=2)

        if not relevant_pubs:
            return "No encontré información relevante sobre ese tema en las publicaciones recientes."

        response_lines = []

        # Primera publicación (la más relevante)
        pub1, score1 = relevant_pubs[0]
        response_lines.append("🔍 Este es el resultado más acorde a tu pregunta: \n")
        response_lines.append(pub1)

        # Segunda publicación (opcional)
        if len(relevant_pubs) > 1:
            pub2, score2 = relevant_pubs[1]
            response_lines.append("\n\n\n... Relacionado con tu búsqueda...")
            response_lines.append(pub2)

        return "\n\n".join(response_lines)

    
    def run_chat(self):
        """Ejecuta el chatbot en modo interactivo"""
        print("\n🤖 Chatbot del TecNM León - Escribe 'salir' para terminar\n")
        
        while True:
            query = input("\nTú: ").strip()
            
            if query.lower() in ['salir', 'exit', 'quit']:
                print("👋 ¡Hasta luego!")
                break
                
            if not query:
                continue
                
            print("\n🤖 Bot: ", end='')
            response = self.generate_response(query)
            print(response)

if __name__ == "__main__":
    chatbot = ChatbotTecNM()
    chatbot.run_chat()