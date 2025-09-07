from sqlalchemy.orm import Session
from app.db.init_db import Review
import h3
import logging
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
from typing import List, Dict
from collections import defaultdict

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define topic labels with their keywords
TOPIC_KEYWORDS = {
    "Cocina Tradicional": ["casero", "tradicional", "típico", "auténtico"],
    "Bar & Copas": ["bar", "copa", "trago", "cerveza", "vino", "cocktail"],
    "Ambiente Moderno": ["moderno", "diseño", "ambiente", "música", "decoración"],
    "Gastronomía Gourmet": ["gourmet", "chef", "creativo", "refinado", "elegante"],
    "Casual & Económico": ["casual", "económico", "simple", "rápido", "informal"]
}

def preprocess_text(text: str) -> str:
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
    text = re.sub(r'[^\w\s\d\-_áéíóúüñÁÉÍÓÚÜÑ]', ' ', text)
    return ' '.join(text.split())

def get_topic_scores(text: str) -> Dict[str, float]:
    text = preprocess_text(text)
    scores = {}
    
    for topic, keywords in TOPIC_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in text)
        scores[topic] = score
    
    # Normalizar puntuaciones
    total = sum(scores.values()) or 1
    return {k: v/total for k, v in scores.items()}

def find_similar_places(reviews: List[Review], target_review: Review, n_similar: int = 5) -> List[Dict]:
    """Encuentra lugares similares usando TF-IDF y similitud coseno"""
    texts = [preprocess_text(f"{r.name} {r.text}") for r in reviews]
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=2)
    tfidf_matrix = vectorizer.fit_transform(texts)
    
    # Calcular similitudes
    target_idx = reviews.index(target_review)
    similarities = cosine_similarity(tfidf_matrix[target_idx:target_idx+1], tfidf_matrix).flatten()
    
    # Obtener los índices de los lugares más similares
    similar_indices = similarities.argsort()[::-1][1:n_similar+1]
    
    return [
        {
            "id": reviews[idx].id,
            "place_id": reviews[idx].place_id,
            "name": reviews[idx].name,
            "lat": float(reviews[idx].lat) if reviews[idx].lat else None,
            "lon": float(reviews[idx].lon) if reviews[idx].lon else None,
            "rating": float(reviews[idx].rating) if reviews[idx].rating else None,
            "topic": reviews[idx].topic,
            "similarity_score": float(similarities[idx])
        }
        for idx in similar_indices
    ]

def run_topic_modeling(db: Session):
    """
    Ejecuta el análisis de tópicos usando keywords y TF-IDF para similitud
    """
    reviews = db.query(Review).filter(Review.text.isnot(None)).all()
    if not reviews:
        logger.info("No hay reseñas para procesar.")
        return None

    logger.info(f"Procesando {len(reviews)} reseñas...")
    
    # Actualizar la base de datos
    updated = 0
    topic_distribution = defaultdict(int)
    
    for review in reviews:
        # Obtener topic scores
        topic_scores = get_topic_scores(f"{review.name} {review.text}")
        # Asignar el topic con mayor score
        review.topic = max(topic_scores.items(), key=lambda x: x[1])[0]
        topic_distribution[review.topic] += 1
        
        # Calcular H3
        if review.lat is not None and review.lon is not None:
            try:
                review.h3_index = h3.geo_to_h3(float(review.lat), float(review.lon), 7)
            except Exception as e:
                logger.error(f"Error calculando H3 para review {review.id}: {e}")
                review.h3_index = None
        
        updated += 1

    db.commit()
    logger.info(f"Topics y H3 asignados a {updated} reseñas.")
    
    # Log topic distribution
    logger.info("Distribución de topics:")
    for topic, count in topic_distribution.items():
        logger.info(f"Topic {topic}: {count} reseñas")
    
    return True

def get_similar_places(db: Session, place_id: str) -> List[Dict]:
    """
    Obtiene lugares similares para un lugar específico
    """
    review = db.query(Review).filter(Review.place_id == place_id).first()
    if not review or not review.similar_places:
        return []
    
    similar_reviews = db.query(Review).filter(Review.id.in_(review.similar_places)).all()
    return [
        {
            "id": r.id,
            "place_id": r.place_id,
            "name": r.name,
            "lat": float(r.lat) if r.lat else None,
            "lon": float(r.lon) if r.lon else None,
            "rating": float(r.rating) if r.rating else None,
            "topic": TOPIC_LABELS.get(r.topic, "Sin clasificar"),
            "similarity_score": float(
                cosine_similarity(
                    [r.embedding], 
                    [review.embedding]
                )[0][0]
            ) if r.embedding and review.embedding else 0.0
        }
        for r in similar_reviews
    ]