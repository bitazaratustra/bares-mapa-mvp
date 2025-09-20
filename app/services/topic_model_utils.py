from typing import List, Dict
from sqlalchemy.orm import Session
from app.db.init_db import Review
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import re
import nltk
import json
from nltk.corpus import stopwords

# Descargar stopwords si no están disponibles
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

STOPWORDS = set(stopwords.words("spanish"))

def preprocess(text):
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
    global model
    if model is None:
        model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    return model

def precompute_embeddings(db: Session):
    """Precompute and store embeddings for all reviews"""
    model = get_model()
    reviews = db.query(Review).filter(Review.text.isnot(None)).all()
    
    for review in reviews:
        text = preprocess(f"{review.name} {review.text}")
        embedding = model.encode(text)
        review.embedding = json.dumps(embedding.tolist())
    
    db.commit()
    print(f"Precomputed embeddings for {len(reviews)} reviews")

def find_similar_to_query(db: Session, query: str, neighborhood: str = None, 
                         min_rating: float = 4.0, n_similar: int = 10) -> List[Dict]:
    """Optimized similarity search using precomputed embeddings"""
    # Filter reviews first
    query_obj = db.query(Review).filter(Review.embedding.isnot(None))
    
    if neighborhood and neighborhood != "Todos":
        query_obj = query_obj.filter(Review.name.ilike(f"%{neighborhood}%"))
    if min_rating > 0:
        query_obj = query_obj.filter(Review.rating >= min_rating)
    
    reviews = query_obj.all()
    
    if not reviews:
        return []

    # Encode query
    model = get_model()
    processed_query = preprocess(query)
    query_embedding = model.encode([processed_query])[0]
    
    # Calculate similarities
    results = []
    for review in reviews:
        try:
            review_embedding = np.array(json.loads(review.embedding))
            similarity = cosine_similarity([query_embedding], [review_embedding])[0][0]
            
            if similarity > 0.3:
                results.append({
                    "place_id": review.place_id,
                    "name": review.name,
                    "lat": float(review.lat) if review.lat else None,
                    "lon": float(review.lon) if review.lon else None,
                    "rating": float(review.rating) if review.rating else None,
                    "text": review.text,
                    "topic": review.topic,
                    "similarity_score": float(similarity)
                })
        except (json.JSONDecodeError, TypeError) as e:
            print(f"Error processing embedding for review {review.id}: {e}")
            continue
    
    # Return top N results
    return sorted(results, key=lambda x: x["similarity_score"], reverse=True)[:n_similar]

def run_topic_modeling(db: Session):
    """Ejecuta modelado de tópicos (opcional para clasificación adicional)"""
    from bertopic import BERTopic
    
    reviews = db.query(Review).filter(Review.text != None).all()
    if not reviews:
        return None

    # Preprocesar textos
    texts = [preprocess(f"{r.name} {r.text}") for r in reviews]
    
    # Generar embeddings
    model = get_model()
    embeddings = model.encode(texts, show_progress_bar=True)

    # Aplicar BERTopic
    topic_model = BERTopic(language="multilingual")
    topics, probs = topic_model.fit_transform(texts, embeddings)
    
    # Asignar tópicos a las reseñas
    for idx, review in enumerate(reviews):
        topic_idx = topics[idx]
        topic_words = topic_model.get_topic(topic_idx)
        if topic_words:
            topic_label = " | ".join([word for word, _ in topic_words[:3]])
        else:
            topic_label = "Sin clasificar"
        review.topic = topic_label

    db.commit()
    return topic_model