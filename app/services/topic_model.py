from typing import List, Dict, Any, Optional
import json
from sqlalchemy.orm import Session
from app.models.review import Review
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import h3
from app.services.text_processing import preprocess_review

MODEL_NAME = "paraphrase-MiniLM-L3-v2"
BATCH_SIZE = 8
SIMILARITY_THRESHOLD = 0.2
MAX_RESULTS = 20
N_TOPICS = 15
MIN_CLUSTER_SIZE = 3
DEFAULT_N_SIMILAR = 10

_model = None

def get_model() -> SentenceTransformer:
    """Devuelve el modelo SentenceTransformer como singleton.

    Usa la CPU y desactiva el paralelismo del tokenizer para no tener picos de memoria.
    """
    global _model
    if _model is None:
        import os
        os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
        _model = SentenceTransformer(MODEL_NAME, device='cpu')
    return _model


def process_in_batches(items: List[Any], batch_size: int = BATCH_SIZE):
    """Divide una lista en batches para procesar sin comerse toda la RAM."""
    for i in range(0, len(items), batch_size):
        yield items[i:i + batch_size]


def precompute_embeddings(db: Session) -> bool:
    """Calcula y guarda embeddings para reseñas que todavía no los tienen.

    Lee las reseñas sin embedding, las procesa en batches, calcula los vectores
    con SentenceTransformer y los guarda como JSON en la base de datos.
    """
    model = get_model()
    reviews = db.query(Review).filter(Review.text.isnot(None), Review.embedding.is_(None)).all()

    print(f"[Embeddings] {len(reviews)} reseñas a procesar (batch={BATCH_SIZE})")
    processed = 0

    for batch in process_in_batches(reviews, BATCH_SIZE):
        texts = [f"{r.name or ''} {r.text or ''}".strip() for r in batch]
        try:
            embeddings = model.encode(
                texts,
                batch_size=BATCH_SIZE,
                show_progress_bar=False,
                convert_to_numpy=True,
                device='cpu'
            )
            for review, embedding in zip(batch, embeddings):
                review.embedding = json.dumps(embedding.tolist())
        except Exception as e:
            print(f"[Embeddings] Error encode batch: {e}. Intento uno a uno...")
            for review, txt in zip(batch, texts):
                try:
                    emb = model.encode(txt, show_progress_bar=False, convert_to_numpy=True, device='cpu')
                    review.embedding = json.dumps(emb.tolist())
                except Exception as e2:
                    print(f"[Embeddings] Error en reseña {getattr(review,'id',None)}: {e2}")
                    continue

        db.commit()
        processed += len(batch)
        print(f"[Embeddings] {processed}/{len(reviews)} procesadas")

    print("[Embeddings] OK")
    return True


def find_similar_to_query(db: Session, query: str, neighborhood: Optional[str] = None, min_rating: float = 0.0, n_similar: int = MAX_RESULTS) -> List[Dict]:
    """Recibe una consulta y devuelve los lugares más parecidos.

    Procesa la consulta, genera su embedding con el mismo modelo que las reseñas,
    compara por similitud coseno contra los embeddings guardados y devuelve los
    mejores resultados ordenados. Se puede filtrar por rating mínimo.
    """
    print(f"[Search] Query: '{query}', min_rating: {min_rating}")

    query_obj = db.query(Review).filter(Review.embedding.isnot(None))
    if not query or query.strip() == "":
        query_obj = query_obj.order_by(Review.rating.desc())
    if neighborhood and neighborhood != "Todos":
        query_obj = query_obj.filter(Review.name.ilike(f"%{neighborhood}%"))
    if min_rating > 0:
        query_obj = query_obj.filter(Review.rating >= min_rating)

    reviews = query_obj.all()
    print(f"[Search] {len(reviews)} reseñas para comparar")
    if not reviews:
        return []

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

    model = get_model()
    query_embedding = model.encode(f"{query}".strip())
    print("[Search] Embedding de la consulta listo")

    results = []
    for batch in process_in_batches(reviews):
        batch_embeddings = np.array([np.array(json.loads(r.embedding)) for r in batch])
        similarities = cosine_similarity([query_embedding], batch_embeddings)[0]

        for review, similarity in zip(batch, similarities):
            if similarity > SIMILARITY_THRESHOLD:
                rating = float(review.rating) if review.rating else 0.0
                rating_norm = rating / 5.0
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

    results.sort(key=lambda x: x.get("score", x.get("similarity_score", 0.0)), reverse=True)
    return results[:n_similar]


def get_similar_reviews(db: Session, review_id: int, n: int = DEFAULT_N_SIMILAR) -> List[Dict]:
    """Devuelve reseñas similares a una reseña dada (por id).

    Calcula similitud coseno entre el embedding de la reseña fuente y el resto,
    y devuelve una lista con las N más parecidas.
    """
    source = db.query(Review).filter(Review.id == review_id).first()
    if not source or not source.embedding:
        return []

    reviews = db.query(Review).filter(Review.embedding.isnot(None), Review.id != review_id).all()
    if not reviews:
        return []

    source_embedding = np.array(json.loads(source.embedding))
    results = []

    for batch in process_in_batches(reviews):
        batch_embeddings = np.array([np.array(json.loads(r.embedding)) for r in batch])
        similarities = cosine_similarity([source_embedding], batch_embeddings)[0]

        for review, sim in zip(batch, similarities):
            if sim > SIMILARITY_THRESHOLD:
                results.append({"review": review, "similarity": float(sim)})

    results.sort(key=lambda x: x["similarity"], reverse=True)
    return [(r["review"], r["similarity"]) for r in results[:n]]


def run_topic_modeling(db: Session, n_topics: int = N_TOPICS) -> bool:
    """Agrupa reseñas en tópicos usando KMeans sobre los embeddings.

    Ajusta el número de tópicos si hay pocos datos, calcula labels con KMeans,
    extrae palabras representativas por cluster y actualiza cada reseña con su
    tópico y su índice H3 si tiene coordenadas.
    """
    print(f"[TopicModeling] Inicio con {n_topics} tópicos...")

    missing_count = db.query(Review).filter(Review.text.isnot(None), Review.embedding.is_(None)).count()
    if missing_count > 0:
        print(f"[TopicModeling] {missing_count} reseñas sin embedding. Calculando...")
        precompute_embeddings(db)

    reviews = db.query(Review).filter(Review.embedding.isnot(None)).all()
    if not reviews:
        print("[TopicModeling] No hay reseñas para procesar")
        return False

    if len(reviews) < n_topics * MIN_CLUSTER_SIZE:
        adjusted_topics = max(2, len(reviews) // MIN_CLUSTER_SIZE)
        print(f"[TopicModeling] Ajustando tópicos a {adjusted_topics}")
        n_topics = adjusted_topics

    embeddings = np.array([np.array(json.loads(r.embedding)) for r in reviews])

    kmeans = KMeans(n_clusters=n_topics, random_state=42, n_init=10, max_iter=300)
    labels = kmeans.fit_predict(embeddings)

    cluster_texts = [[] for _ in range(n_topics)]
    cluster_sizes = [0] * n_topics
    for i, review in enumerate(reviews):
        cluster_texts[labels[i]].append(preprocess_review(review.text, review.name))
        cluster_sizes[labels[i]] += 1

    print("Distribución de clusters:")
    for i, size in enumerate(cluster_sizes):
        print(f"Cluster {i}: {size} reseñas")

    processed = 0
    for batch_start in range(0, len(reviews), BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, len(reviews))
        batch = reviews[batch_start:batch_end]
        batch_labels = labels[batch_start:batch_end]

        for review, label in zip(batch, batch_labels):
            texts_in_cluster = ' '.join(cluster_texts[label])
            words = texts_in_cluster.split()

            word_freq = {}
            for word in set(words):
                tf = words.count(word)
                other_clusters_with_word = sum(1 for i in range(n_topics) if i != label and word in ' '.join(cluster_texts[i]))
                significance = tf * (1.0 / (1.0 + other_clusters_with_word))
                word_freq[word] = significance

            significant_words = sorted(word_freq.items(), key=lambda x: -x[1])[:4]
            selected_words = [w for w, _ in significant_words]

            review.topic = f"Topic {label}: {', '.join(selected_words)}"

            if review.lat is not None and review.lon is not None:
                try:
                    review.h3_index = h3.geo_to_h3(float(review.lat), float(review.lon), 7)
                except Exception as e:
                    print(f"Error H3 reseña {getattr(review,'id',None)}: {e}")
                    review.h3_index = None

            processed += 1

        db.commit()
        print(f"[TopicModeling] {processed}/{len(reviews)} procesadas")

    print("[TopicModeling] OK")
    return True
