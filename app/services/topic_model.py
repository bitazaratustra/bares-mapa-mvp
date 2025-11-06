from typing import List, Dict
from sqlalchemy.orm import Session
from app.db.init_db import Review
from sentence_transformers import SentenceTransformer
from bertopic import BERTopic
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict
import h3
import re
import numpy as np

# Use English stopwords if available, fall back to a small set
try:
    import nltk
    from nltk.corpus import stopwords
    STOPWORDS = set(stopwords.words("english"))
except Exception:
    STOPWORDS = set(["the", "and", "is", "in", "it", "of", "to", "a"]) 


def preprocess(text: str) -> str:
    text = (text or "").lower()
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"[^a-z ]", "", text)
    tokens = text.split()
    tokens = [t for t in tokens if t not in STOPWORDS and len(t) > 2]
    return " ".join(tokens)


def run_topic_modeling(db: Session, model_name: str = "paraphrase-MiniLM-L3-v2"):
    """Run BERTopic over all reviews (English pipeline).

    This function will compute embeddings for any reviews missing them, then
    fit BERTopic and assign topic labels and H3 indices to reviews.
    """
    reviews = db.query(Review).filter(Review.text != None).all()
    if not reviews:
        print("No reviews to process.")
        return None

    print(f"Processing {len(reviews)} reviews for topic modeling...")

    # Precompute embeddings for reviews missing them (if util available)
    missing = db.query(Review).filter(Review.text.isnot(None), Review.embedding.is_(None)).count()
    if missing > 0:
        print(f"Found {missing} reviews without embeddings — computing embeddings before topic modeling...")
        try:
            from app.services.topic_model_utils import precompute_embeddings
            precompute_embeddings(db)
        except Exception as e:
            print(f"Could not precompute embeddings via topic_model_utils: {e}")

    # Refresh reviews list now that embeddings may exist
    reviews = db.query(Review).filter(Review.embedding.isnot(None)).all()
    texts = [preprocess(f"{r.name} {r.text}") for r in reviews]

    if not texts:
        print("No texts with embeddings found after precompute.")
        return None

    # Build embeddings using a lightweight English model
    model = SentenceTransformer(model_name)
    embeddings = model.encode(texts, show_progress_bar=True)

    # Fit BERTopic
    topic_model = BERTopic(language="english")
    topics, probs = topic_model.fit_transform(texts, embeddings)

    # Assign topics and H3 indices
    topic_distribution = defaultdict(int)
    updated = 0
    for idx, review in enumerate(reviews):
        topic_idx = topics[idx]
        topic_words = topic_model.get_topic(topic_idx)
        if topic_words:
            topic_label = " | ".join([word for word, _ in topic_words[:3]])
        else:
            topic_label = "Unassigned"
        review.topic = topic_label
        topic_distribution[topic_label] += 1

        # H3 index
        if review.lat is not None and review.lon is not None:
            try:
                review.h3_index = h3.geo_to_h3(float(review.lat), float(review.lon), 7)
            except Exception as e:
                print(f"Error computing H3 for review {review.id}: {e}")
                review.h3_index = None
        updated += 1

    db.commit()
    print(f"Assigned topics and H3 to {updated} reviews.")
    print("Topic distribution:")
    for t, c in topic_distribution.items():
        print(f"{t}: {c}")

    return topic_model


def find_similar_places(reviews: List[Review], topic: str, db: Session, model_name: str = "paraphrase-MiniLM-L3-v2") -> List[Dict]:
    """Find places similar to a given topic using embedding similarity."""
    try:
        review_texts = [preprocess(f"{r.name} {r.text}") for r in reviews]
        if not review_texts:
            return []

        model = SentenceTransformer(model_name)
        review_embeddings = model.encode(review_texts, convert_to_tensor=True, show_progress_bar=False)

        topic_reviews = db.query(Review).filter(Review.topic == topic).all()
        if topic_reviews:
            topic_texts = [preprocess(f"{r.name} {r.text}") for r in topic_reviews]
            topic_embedding = model.encode(topic_texts[0], convert_to_tensor=True, show_progress_bar=False)
        else:
            topic_embedding = model.encode(topic, convert_to_tensor=True, show_progress_bar=False)

        similarities = cosine_similarity(
            topic_embedding.cpu().numpy().reshape(1, -1),
            review_embeddings.cpu().numpy()
        )[0]

        similar_indices = np.argsort(similarities)[::-1]
        results = []
        seen = set()
        for idx in similar_indices:
            review = reviews[idx]
            if review.place_id in seen:
                continue
            if similarities[idx] > 0.3:
                seen.add(review.place_id)
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
            if len(results) >= 10:
                break
        return results
    except Exception as e:
        print(f"Error in find_similar_places: {e}")
        return []


def find_similar_to_query(db: Session, query: str, neighborhood: str = None, min_rating: float = 0, n_similar: int = 10, model_name: str = "paraphrase-MiniLM-L3-v2") -> List[Dict]:
    reviews = db.query(Review).filter(Review.text.isnot(None))
    if neighborhood:
        reviews = reviews.filter(Review.name.ilike(f"%{neighborhood}%"))
    if min_rating > 0:
        reviews = reviews.filter(Review.rating >= min_rating)
    reviews = reviews.all()
    if not reviews:
        return []

    texts = [preprocess(f"{r.name} {r.text}") for r in reviews]
    model = SentenceTransformer(model_name)
    query_embedding = model.encode([preprocess(query)], show_progress_bar=False)
    reviews_embeddings = model.encode(texts, show_progress_bar=False)

    similarities = cosine_similarity(query_embedding, reviews_embeddings).flatten()
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
    

