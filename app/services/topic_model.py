from typing import List, Dict
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.init_db import Review
from sentence_transformers import SentenceTransformer
import torch
from bertopic import BERTopic
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict
import h3
import re
import nltk
import numpy as np

#nltk.download("stopwords")
from nltk.corpus import stopwords

STOPWORDS = set(stopwords.words("spanish"))

def preprocess(text):
    text = text.lower()
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"[^a-záéíóúüñ ]", "", text)
    tokens = text.split()
    tokens = [t for t in tokens if t not in STOPWORDS]
    return " ".join(tokens)

def run_topic_modeling(db: Session):
    """
    Ejecuta el análisis de tópicos usando BERTopic y embeddings multilingües
    """
    reviews = db.query(Review).filter(Review.text != None).all()
    if not reviews:
        print("No hay reseñas para procesar.")
        return None

    print(f"Procesando {len(reviews)} reseñas...")
    
    # Preprocesar textos
    texts = [preprocess(f"{r.name} {r.text}") for r in reviews]
    
    # Generar embeddings
    model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    embeddings = model.encode(texts, show_progress_bar=True)

    # Aplicar BERTopic
    topic_model = BERTopic(language="multilingual")
    topics, probs = topic_model.fit_transform(texts, embeddings)
    
    # Obtener y guardar tópicos
    updated = 0
    topic_distribution = defaultdict(int)
    
    for idx, review in enumerate(reviews):
        topic_idx = topics[idx]
        # Obtener las palabras más representativas del tópico
        topic_words = topic_model.get_topic(topic_idx)
        if topic_words:
            # Usar las 3 palabras más relevantes como etiqueta
            topic_label = " | ".join([word for word, _ in topic_words[:3]])
        else:
            topic_label = "Sin clasificar"
        review.topic = topic_label
        topic_distribution[topic_label] += 1
        
        # Calcular H3
        if review.lat is not None and review.lon is not None:
            try:
                review.h3_index = h3.geo_to_h3(float(review.lat), float(review.lon), 7)
            except Exception as e:
                print(f"Error calculando H3 para review {review.id}: {e}")
                review.h3_index = None
        
        updated += 1

    db.commit()
    print(f"Topics y H3 asignados a {updated} reseñas.")
    
    # Log topic distribution
    print("Distribución de topics:")
    for topic, count in topic_distribution.items():
        print(f"Topic {topic}: {count} reseñas")
    
    return topic_model

def find_similar_places(reviews: List[Review], topic: str, db: Session) -> List[Dict]:
    """
    Encuentra lugares similares basados en el tópico seleccionado usando BERTopic
    """
    try:
        # Preprocesar y generar embeddings para las reseñas del barrio
        review_texts = [preprocess(f"{r.name} {r.text}") for r in reviews]
        if not review_texts:
            return []

        # Modelo para embeddings
        model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
        
        # Generar embeddings para las reseñas
        review_embeddings = model.encode(review_texts, convert_to_tensor=True, show_progress_bar=False)
        
        # Obtener el embedding del tópico (usando las reseñas existentes con ese tópico)
        topic_reviews = db.query(Review).filter(Review.topic == topic).all()
        if topic_reviews:
            topic_texts = [preprocess(f"{r.name} {r.text}") for r in topic_reviews]
            topic_embedding = model.encode(topic_texts[0], convert_to_tensor=True, show_progress_bar=False)
        else:
            # Si no hay reseñas con ese tópico, usar el texto del tópico directamente
            topic_embedding = model.encode(topic, convert_to_tensor=True, show_progress_bar=False)
    
        # Calcular similitudes usando cosine_similarity
        similarities = cosine_similarity(
            topic_embedding.cpu().numpy().reshape(1, -1),
            review_embeddings.cpu().numpy()
        )[0]
        
        # Ordenar por similitud
        similar_indices = np.argsort(similarities)[::-1]
        
        # Preparar resultados
        results = []
        seen_places = set()
        
        for idx in similar_indices:
            review = reviews[idx]
            if review.place_id not in seen_places and similarities[idx] > 0.3:  # umbral de similitud
                seen_places.add(review.place_id)
                results.append({
                    "place_id": review.place_id,
                    "name": review.name,
                    "rating": review.rating,
                    "topic": review.topic,
                    "similarity_score": float(similarities[idx]),
                    "lat": review.lat,
                    "lon": review.lon,
                    "text": review.text
                })
                
                if len(results) >= 10:  # límite de resultados
                    break
                    
        return results
        
    except Exception as e:
        print(f"Error en find_similar_places: {str(e)}")
        return []
                
    return results

def find_similar_to_query(db: Session, query: str, neighborhood: str = None, min_rating: float = 0, n_similar: int = 10) -> List[Dict]:
    """Encuentra lugares similares a una consulta de texto"""
    reviews = db.query(Review).filter(Review.text.isnot(None))
    
    if neighborhood:
        reviews = reviews.filter(Review.name.ilike(f"%{neighborhood}%"))
    if min_rating > 0:
        reviews = reviews.filter(Review.rating >= min_rating)
    
    reviews = reviews.all()
    if not reviews:
        return []

    # Preprocesar textos
    texts = [preprocess(f"{r.name} {r.text}") for r in reviews]
    
    # Generar embeddings
    model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    query_embedding = model.encode([preprocess(query)], show_progress_bar=False)
    reviews_embeddings = model.encode(texts, show_progress_bar=False)
    
    # Calcular similitudes
    similarities = cosine_similarity(query_embedding, reviews_embeddings).flatten()
    
    # Obtener los índices de los lugares más similares
    similar_indices = similarities.argsort()[::-1][:n_similar]
    
    return [
        {
            "place_id": reviews[idx].place_id,
            "name": reviews[idx].name,
            "lat": float(reviews[idx].lat) if reviews[idx].lat else None,
            "lon": float(reviews[idx].lon) if reviews[idx].lon else None,
            "rating": float(reviews[idx].rating) if reviews[idx].rating else None,
            "text": reviews[idx].text,
            "topic": reviews[idx].topic,
            "similarity_score": float(similarities[idx])
        }
        for idx in similar_indices
    ]
   