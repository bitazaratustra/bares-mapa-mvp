from typing import List, Dict
import json
from sqlalchemy.orm import Session
from app.db.init_db import Review
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from sklearn.cluster import KMeans
import re
import nltk
from nltk.corpus import stopwords
import numpy as np

# Configuración global
MODEL_NAME = "paraphrase-MiniLM-L3-v2"  # Modelo más ligero para máquinas con pocos recursos
BATCH_SIZE = 8  # Para procesar en lotes (reducido para menor consumo de RAM/CPU)
SIMILARITY_THRESHOLD = 0.2  # Umbral más permisivo para mostrar más resultados
MAX_RESULTS = 20  # Aumentamos el número máximo de resultados
N_TOPICS = 15  # Número de tópicos para el clustering
MIN_CLUSTER_SIZE = 3  # Mínimo número de reseñas por cluster

# Inicializar stopwords
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')
STOPWORDS = set(stopwords.words("spanish"))

def preprocess(text):
    """Preprocesa el texto para análisis"""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"[^a-záéíóúüñ ]", "", text)
    tokens = text.split()
    tokens = [t for t in tokens if t not in STOPWORDS and len(t) > 2]
    return " ".join(tokens)

model = None

def get_model():
    """Singleton para el modelo de embeddings"""
    global model
    if model is None:
        # Force CPU usage and disable tokenizer parallelism to reduce memory spikes
        import os
        os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
        model = SentenceTransformer(MODEL_NAME, device='cpu')
    return model

def process_in_batches(items, batch_size=BATCH_SIZE):
    """Procesa una lista en lotes"""
    for i in range(0, len(items), batch_size):
        yield items[i:i + batch_size]

def precompute_embeddings(db: Session):
    """Precomputa embeddings para todas las reseñas usando procesamiento por lotes"""
    import json
    model = get_model()
    reviews = db.query(Review).filter(Review.text.isnot(None)).all()
    
    print(f"[Embeddings] Procesando {len(reviews)} reseñas en lotes de {BATCH_SIZE}...")
    processed = 0
    
    for batch in process_in_batches(reviews, BATCH_SIZE):
        texts = [preprocess(f"{r.name} {r.text}") for r in batch]
        try:
            # Use convert_to_numpy to avoid keeping tensors on GPU and reduce memory
            embeddings = model.encode(texts, batch_size=BATCH_SIZE, show_progress_bar=False, convert_to_numpy=True, device='cpu')
            for review, embedding in zip(batch, embeddings):
                # Convertir el embedding a texto JSON
                review.embedding = json.dumps(embedding.tolist())

        except MemoryError as me:
            print(f"[Embeddings] MemoryError durante encode batch: {me}. Intentando en modo seguro (uno a uno)...")
            for review, txt in zip(batch, texts):
                try:
                    emb = model.encode(txt, show_progress_bar=False, convert_to_numpy=True, device='cpu')
                    review.embedding = json.dumps(emb.tolist())
                except Exception as e:
                    print(f"[Embeddings] Error codificando reseña {review.id}: {e}")
                    continue
        except Exception as e:
            # Fallback: try encoding one-by-one which uses less peak memory
            print(f"[Embeddings] Error durante encode batch: {e}. Reintentando uno a uno...")
            for review, txt in zip(batch, texts):
                try:
                    emb = model.encode(txt, show_progress_bar=False, convert_to_numpy=True, device='cpu')
                    review.embedding = json.dumps(emb.tolist())
                except Exception as e2:
                    print(f"[Embeddings] Error codificando reseña {review.id}: {e2}")
                    continue
        
        db.commit()
        processed += len(batch)
        print(f"[Embeddings] {processed}/{len(reviews)} reseñas procesadas")

    print("[Embeddings] Proceso completado")
    return True


def find_similar_to_query(db: Session, query: str, neighborhood: str = None, 
                         min_rating: float = 0.0, n_similar: int = MAX_RESULTS) -> List[Dict]:
    """Busca lugares similares a una consulta usando embeddings precomputados"""
    print(f"[Search] Iniciando búsqueda - Query: '{query}', Barrio: '{neighborhood}', Rating mínimo: {min_rating}")
    
    # Filtrar reseñas
    query_obj = db.query(Review).filter(Review.embedding.isnot(None))
    
    # Si no hay query, mostrar los mejor valorados
    if not query or query.strip() == "":
        query_obj = query_obj.order_by(Review.rating.desc())
    
    if neighborhood and neighborhood != "Todos":
        query_obj = query_obj.filter(Review.name.ilike(f"%{neighborhood}%"))
    if min_rating > 0:
        query_obj = query_obj.filter(Review.rating >= min_rating)
    
    reviews = query_obj.all()
    print(f"[Search] Encontradas {len(reviews)} reseñas que cumplen los filtros")
    
    if not reviews:
        return []

    # Si no hay query, devolver los mejores valorados
    if not query or query.strip() == "":
        return [{
            "place_id": r.place_id,
            "name": r.name,
            "lat": float(r.lat) if r.lat else None,
            "lon": float(r.lon) if r.lon else None,
            "rating": float(r.rating) if r.rating else None,
            "text": r.text,
            "topic": r.topic,
            "similarity_score": 1.0
        } for r in reviews[:n_similar]]

    # Generar embedding para la consulta
    model = get_model()
    query_embedding = model.encode(preprocess(query))
    print("[Search] Embedding generado para la consulta")
    
    # Calcular similitudes en lotes
    results = []
    for batch in process_in_batches(reviews):
        batch_embeddings = np.array([np.array(json.loads(r.embedding)) for r in batch])
        similarities = cosine_similarity([query_embedding], batch_embeddings)[0]
        
        # Almacenar resultados relevantes
        for i, (review, similarity) in enumerate(zip(batch, similarities)):
            if similarity > SIMILARITY_THRESHOLD:
                # Combine similarity with rating to improve ranking
                rating = float(review.rating) if review.rating else 0.0
                rating_norm = rating / 5.0  # normalize to [0,1]
                # weighted score: 70% similarity, 30% rating
                combined_score = 0.7 * float(similarity) + 0.3 * rating_norm
                results.append({
                    "place_id": review.place_id,
                    "name": review.name,
                    "lat": float(review.lat) if review.lat else None,
                    "lon": float(review.lon) if review.lon else None,
                    "rating": rating,
                    "text": review.text,
                    "topic": review.topic,
                    "similarity_score": float(similarity),
                    "score": float(combined_score)
                })
    
    # Ordenar por similitud y retornar los mejores
    # Sort by combined score if present, otherwise similarity
    results.sort(key=lambda x: x.get("score", x.get("similarity_score", 0.0)), reverse=True)
    return results[:n_similar]

def run_topic_modeling(db: Session, n_topics: int = N_TOPICS):
    """Agrupa reseñas en tópicos usando KMeans sobre embeddings con validación"""
    print(f"[TopicModeling] Iniciando con {n_topics} tópicos...")
    
    # Asegurarse de que todas las reseñas tienen embeddings
    missing_count = db.query(Review).filter(Review.text.isnot(None), Review.embedding.is_(None)).count()
    if missing_count > 0:
        print(f"[TopicModeling] Encontradas {missing_count} reseñas sin embeddings. Precomputando embeddings antes de modelar...")
        precompute_embeddings(db)

    # Obtener reseñas con embeddings
    reviews = db.query(Review).filter(Review.embedding.isnot(None)).all()
    if not reviews:
        print("[TopicModeling] No hay reseñas con embeddings para procesar")
        return False

    if len(reviews) < n_topics * MIN_CLUSTER_SIZE:
        adjusted_topics = max(2, len(reviews) // MIN_CLUSTER_SIZE)
        print(f"[TopicModeling] Ajustando número de tópicos a {adjusted_topics} debido al tamaño de datos")
        n_topics = adjusted_topics

    # Convertir embeddings a matriz numpy
    embeddings = np.array([np.array(json.loads(r.embedding)) for r in reviews])
    
    # Aplicar KMeans con múltiples inicializaciones
    kmeans = KMeans(n_clusters=n_topics, random_state=42, n_init=10, max_iter=300)
    labels = kmeans.fit_predict(embeddings)
    
    # Encontrar las palabras más representativas por cluster
    cluster_texts = [[] for _ in range(n_topics)]
    cluster_sizes = [0] * n_topics
    for i, review in enumerate(reviews):
        cluster_texts[labels[i]].append(preprocess(f"{review.name} {review.text}"))
        cluster_sizes[labels[i]] += 1
    
    print("\nDistribución de clusters:")
    for i, size in enumerate(cluster_sizes):
        print(f"Cluster {i}: {size} reseñas")
    
    # Asignar tópicos y guardar
    processed = 0
    for batch_start in range(0, len(reviews), BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, len(reviews))
        batch = reviews[batch_start:batch_end]
        batch_labels = labels[batch_start:batch_end]
        
        for review, label in zip(batch, batch_labels):
            # Obtener palabras más comunes y significativas del cluster
            texts_in_cluster = ' '.join(cluster_texts[label])
            words = texts_in_cluster.split()
            
            # Calcular TF-IDF simplificado
            word_freq = {}
            for word in set(words):
                # TF: frecuencia en este cluster
                tf = words.count(word)
                # IDF: en cuántos otros clusters aparece
                other_clusters_with_word = sum(
                    1 for i in range(n_topics) 
                    if i != label and word in ' '.join(cluster_texts[i])
                )
                # Penalizar palabras que aparecen en muchos clusters
                significance = tf * (1.0 / (1.0 + other_clusters_with_word))
                word_freq[word] = significance
            
            # Seleccionar las palabras más significativas
            significant_words = sorted(word_freq.items(), key=lambda x: -x[1])[:4]
            selected_words = [w for w, _ in significant_words]
            
            review.topic = f"Topic {label}: {', '.join(selected_words)}"
            processed += 1
            
        db.commit()
        print(f"[TopicModeling] {processed}/{len(reviews)} reseñas procesadas")
    
    print("[TopicModeling] Proceso completado")
    return True