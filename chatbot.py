import os
import re
import unicodedata
import numpy as np
from datetime import datetime
import warnings
import math
from collections import Counter

warnings.filterwarnings('ignore')

# Configuración optimizada
PUBLICACIONES_FILE = os.path.join(os.path.dirname(__file__), "publicaciones_tec.txt")
MAX_PUBLICATIONS = 50

class ChatbotTecNM:
    def __init__(self):
        self.model = self.load_model()
        self.publicaciones = []
        self.embeddings = None
        self.vocab = {}
        self.idf = {}
        self.normalized_publications = []
        self.last_update = None
        self.load_publications()
        
        # Respuesta predefinida para saludos
        self.respuesta_saludo = "¡Hola! 😊 Estoy aquí para ayudarte con cualquier información o pregunta que tengas acerca del TECNM campus 1."

    def load_model(self):
        """Placeholder — no cargamos modelos pesados."""
        return None

    def _normalize_text(self, text):
        """Normaliza el texto para comparación."""
        if text is None:
            return ""
        text = text.lower().strip()
        text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
        text = re.sub(r'[^\w\s]', '', text)  # Remover puntuación
        text = re.sub(r'\s+', ' ', text)      # Reducir múltiples espacios
        return text

    def _es_saludo(self, query):
        """Determina si la consulta es solo un saludo usando palabras clave"""
        query_normalized = self._normalize_text(query)
        if not query_normalized:
            return False
        
        # Palabras clave de saludo
        saludo_keywords = {
            'hola', 'buenos', 'buenas', 'dias', 'tardes', 'noches', 'saludos', 
            'tal', 'hey', 'hello', 'hi', 'bonjour', 'amigo', 'bot', 'maquina', 
            'inteligencia', 'artificial', 'terricola', 'probando', 'ahi', 
            'quien', 'eres', 'soy', 'llamo', 'ayuda', 'ayudar', 'pregunta',
            'preguntas', 'ingles', 'hablas', 'presento', 'nombre', 'llamarme'
        }
        
        # Palabras que indican que no es solo un saludo
        contenido_keywords = {
            'informacion', 'pregunta', 'duda', 'consulta', 'saber', 'necesito',
            'busco', 'quiero', 'donde', 'cuando', 'como', 'quien', 'cual', 'porque',
            'director', 'directora', 'direccion', 'telefono', 'correo', 'contacto',
            'horario', 'fecha', 'examen', 'inscripcion', 'requisito', 'carrera',
            'departamento', 'servicio', 'tramite', 'mapa', 'ubicacion', 'costo'
        }
        
        # Dividir la consulta en palabras
        palabras = set(query_normalized.split())
        
        # Si no hay palabras, no es un saludo
        if not palabras:
            return False
            
        # Verificar si contiene palabras clave de contenido
        if any(palabra in contenido_keywords for palabra in palabras):
            return False
            
        # Verificar si contiene palabras clave de saludo
        if any(palabra in saludo_keywords for palabra in palabras):
            # Contar palabras de contenido en la consulta
            palabras_contenido = sum(1 for palabra in palabras if palabra in contenido_keywords)
            
            # Si tiene menos de 3 palabras o no contiene palabras de contenido
            return len(palabras) <= 5 or palabras_contenido == 0
        
        return False

    def compute_tfidf(self, docs):
        """Calcula TF-IDF"""
        self.normalized_publications = [self._normalize_text(d) for d in docs]
        
        df = Counter()
        for tokens in self.normalized_publications:
            for t in set(tokens):
                df[t] += 1
        
        vocab_list = sorted(df.keys())
        self.vocab = {t: i for i, t in enumerate(vocab_list)}
        
        N = len(docs)
        self.idf = {t: math.log((N + 1) / (df[t] + 1)) + 1 for t in vocab_list}
        
        V = len(vocab_list)
        tfidf_matrix = np.zeros((N, V), dtype=float)
        for i, tokens in enumerate(self.normalized_publications):
            L = len(tokens) if tokens else 1
            tf = Counter(tokens)
            for token, freq in tf.items():
                if token in self.vocab:
                    tf_val = freq / L
                    tfidf_matrix[i, self.vocab[token]] = tf_val * self.idf[token]
        
        self.embeddings = tfidf_matrix

    def load_publications(self):
        """Carga las publicaciones y calcula TF-IDF"""
        try:
            if not os.path.exists(PUBLICACIONES_FILE):
                print("⚠️ Archivo de publicaciones no encontrado")
                return
            
            with open(PUBLICACIONES_FILE, 'r', encoding='utf-8') as f:
                self.publicaciones = [line.strip() for line in f if line.strip()][-MAX_PUBLICATIONS:]
            
            if self.publicaciones:
                print(f"📖 Cargadas {len(self.publicaciones)} publicaciones")
                self.compute_tfidf(self.publicaciones)
            
            self.last_update = datetime.now()
        except Exception as e:
            print(f"⚠️ Error cargando publicaciones: {str(e)}")

    def cosine_similarity(self, a, b):
        """Similitud coseno segura"""
        a = np.asarray(a, dtype=float)
        b = np.asarray(b, dtype=float)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))
    
    def vectorize_query(self, query):
        """Vector TF-IDF para la consulta"""
        tokens = self._normalize_text(query).split()
        vec = np.zeros(len(self.vocab), dtype=float)
        if not tokens or not self.vocab:
            return vec
        tf = Counter(tokens)
        L = len(tokens)
        for token, freq in tf.items():
            if token in self.vocab:
                vec[self.vocab[token]] = (freq / L) * self.idf.get(token, 0.0)
        return vec

    def _substring_fallback(self, query_tokens, top_k):
        """Buscar coincidencias por tokens"""
        matches = []
        if not query_tokens:
            return matches
        for i, tokens in enumerate(self.normalized_publications):
            match_count = sum(1 for t in query_tokens if t in tokens)
            if match_count > 0:
                score = 0.01 + (match_count / len(query_tokens)) * 0.1
                matches.append((i, score, match_count))
        matches.sort(key=lambda x: (x[1], x[2]), reverse=True)
        return [(self.publicaciones[i], s) for i, s, _ in matches[:top_k]]
    
    def get_top_publications(self, query, top_k=2):
        """Obtiene las publicaciones más relevantes"""
        try:
            if not self.publicaciones:
                return []
            
            query_vec = self.vectorize_query(query)
            if query_vec.sum() == 0 or self.embeddings is None or self.embeddings.size == 0:
                qtokens = self._normalize_text(query).split()
                fb = self._substring_fallback(qtokens, top_k)
                if fb:
                    return fb
                return [(self.publicaciones[i], 0.0) for i in range(min(top_k, len(self.publicaciones)))]
            
            sims = [self.cosine_similarity(query_vec, pub_vec) for pub_vec in self.embeddings]
            sims = np.array(sims, dtype=float)
            if sims.max() == 0.0:
                qtokens = self._normalize_text(query).split()
                fb = self._substring_fallback(qtokens, top_k)
                if fb:
                    return fb
                top_indices = np.argsort(sims)[-top_k:][::-1]
                return [(self.publicaciones[i], float(sims[i])) for i in top_indices]
            
            top_indices = np.argsort(sims)[-top_k:][::-1]
            return [(self.publicaciones[i], float(sims[i])) for i in top_indices]
        except Exception as e:
            print(f"⚠️ Error buscando publicaciones: {str(e)}")
            return []
    
    def generate_response(self, query):
        """Genera respuesta, primero verificando si es un saludo"""
        try:
            # Primero verificar si es solo un saludo
            if self._es_saludo(query):
                return self.respuesta_saludo
            
            # Si no es saludo, proceder con la búsqueda normal
            if not self.publicaciones:
                return "No hay publicaciones disponibles. Por favor intenta más tarde."
            
            top_pubs = self.get_top_publications(query)
            if not top_pubs:
                return "No encontré información relevante sobre ese tema."
            
            response = []
            main_pub, main_score = top_pubs[0]
            if main_score < 0.05:
                response.append(f"🔍 Encontré coincidencias pero con baja confianza (confianza: {main_score:.2f}):")
            else:
                response.append(f"🔍 Este es el resultado más relevante (confianza: {main_score:.2f}):")
            response.append(main_pub)
            
            if len(top_pubs) > 1:
                sug_pub, sug_score = top_pubs[1]
                response.append("")
                response.append(f"💡 También te podría interesar (confianza: {sug_score:.2f}):")
                response.append(sug_pub)
            
            return "\n\n".join(response)
        except Exception as e:
            print(f"⚠️ Error generando respuesta: {str(e)}")
            return "Disculpa, ocurrió un error al procesar tu solicitud."