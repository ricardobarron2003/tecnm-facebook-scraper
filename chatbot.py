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
MAX_PUBLICATIONS = 50   # Límite de publicaciones a procesar

class ChatbotTecNM:
    def __init__(self):
        self.model = self.load_model()  # placeholder para compatibilidad
        self.publicaciones = []
        self.embeddings = None          # ahora contiene la matriz TF-IDF
        self.vocab = {}
        self.idf = {}
        self.normalized_publications = []  # lista de tokens normalizados por publicación
        self.last_update = None
        self.load_publications()
    
    def load_model(self):
        """Placeholder — no cargamos modelos pesados."""
        return None

    def _normalize_text(self, text):
        """Lowercase, quitar acentos y extraer tokens alfanuméricos."""
        if text is None:
            return []
        text = text.lower()
        # quitar acentos (normalizar a ascii)
        text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
        # extraer tokens (letras y números)
        tokens = re.findall(r'\w+', text)
        return tokens

    def compute_tfidf(self, docs):
        """Calcula TF-IDF (idf suavizado) y guarda embeddings + vocab + idf + versiones normalizadas"""
        # normalizar documentos
        self.normalized_publications = [self._normalize_text(d) for d in docs]
        
        # document frequency
        df = Counter()
        for tokens in self.normalized_publications:
            for t in set(tokens):
                df[t] += 1
        
        # vocab determinístico (orden alfabético)
        vocab_list = sorted(df.keys())
        self.vocab = {t: i for i, t in enumerate(vocab_list)}
        
        N = len(docs)
        # idf tipo scikit-learn: idf = log((N+1)/(df+1)) + 1  -> evita ceros y estabiliza valores
        self.idf = {t: math.log((N + 1) / (df[t] + 1)) + 1 for t in vocab_list}
        
        # construir matriz TF-IDF
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
        """Vector TF-IDF para la consulta (usa el mismo vocab + idf)"""
        tokens = self._normalize_text(query)
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
        """
        Buscar coincidencias por tokens dentro de publicaciones normalizadas.
        Devuelve una lista de (texto, score) ordenada por count de tokens coincidentes.
        """
        matches = []
        if not query_tokens:
            return matches
        for i, tokens in enumerate(self.normalized_publications):
            # contar cuántos tokens de la query aparecen en la publicación
            match_count = sum(1 for t in query_tokens if t in tokens)
            if match_count > 0:
                # score pequeño pero ordenable (más tokens coincidentes => mayor score)
                score = 0.01 + (match_count / len(query_tokens)) * 0.1
                matches.append((i, score, match_count))
        # ordenar por score y luego por match_count
        matches.sort(key=lambda x: (x[1], x[2]), reverse=True)
        # convertir a (texto, score)
        return [(self.publicaciones[i], s) for i, s, _ in matches[:top_k]]
    
    def get_top_publications(self, query, top_k=2):
        """Obtiene las publicaciones más relevantes (TF-IDF) con fallback por tokens"""
        try:
            # si no hay publicaciones
            if not self.publicaciones:
                return []
            
            query_vec = self.vectorize_query(query)
            # si vocab vacío o vector nulo, usar fallback por tokens
            if query_vec.sum() == 0 or self.embeddings is None or self.embeddings.size == 0:
                qtokens = self._normalize_text(query)
                fb = self._substring_fallback(qtokens, top_k)
                # si fallback encontró resultados, devuélvelos
                if fb:
                    return fb
                # si no, devolver top_k arbitrarios (por si quieres algo aunque sea poco informativo)
                return [(self.publicaciones[i], 0.0) for i in range(min(top_k, len(self.publicaciones)))]
            
            # calcular similitud con cada publicación
            sims = [self.cosine_similarity(query_vec, pub_vec) for pub_vec in self.embeddings]
            sims = np.array(sims, dtype=float)
            # si todas las similitudes son 0 → intentar fallback por tokens
            if sims.max() == 0.0:
                qtokens = self._normalize_text(query)
                fb = self._substring_fallback(qtokens, top_k)
                if fb:
                    return fb
                # si aún no hay matches, devolver los top_k por orden (score 0)
                top_indices = np.argsort(sims)[-top_k:][::-1]
                return [(self.publicaciones[i], float(sims[i])) for i in top_indices]
            
            top_indices = np.argsort(sims)[-top_k:][::-1]
            return [(self.publicaciones[i], float(sims[i])) for i in top_indices]
        except Exception as e:
            print(f"⚠️ Error buscando publicaciones: {str(e)}")
            return []
    
    def generate_response(self, query):
        """Genera respuesta con la publicación principal y una sugerencia"""
        try:
            if not self.publicaciones:
                return "No hay publicaciones disponibles. Por favor intenta más tarde."
            
            top_pubs = self.get_top_publications(query)
            if not top_pubs:
                return "No encontré información relevante sobre ese tema."
            
            response = []
            main_pub, main_score = top_pubs[0]
            # si la confianza es muy baja, indicarlo pero aun así mostrar resultado
            if main_score < 0.05:
                response.append(f"🔍 Encontré coincidencias pero con baja confianza (confianza: {main_score:.2f}):")
            else:
                response.append(f"🔍 Este es el resultado más relevante (confianza: {main_score:.2f}):")
            response.append(main_pub)
            
            # segunda publicación (si existe)
            if len(top_pubs) > 1:
                sug_pub, sug_score = top_pubs[1]
                response.append("")
                response.append(f"💡 También te podría interesar (confianza: {sug_score:.2f}):")
                response.append(sug_pub)
            
            return "\n\n".join(response)
        except Exception as e:
            print(f"⚠️ Error generando respuesta: {str(e)}")
            return "Disculpa, ocurrió un error al procesar tu solicitud."
