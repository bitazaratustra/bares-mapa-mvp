from typing import List, Dict, Any, Optional
import json
from sqlalchemy.orm import Session
from app.models.review import Review
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict
import numpy as np
import h3
from app.services.text_processing import preprocess_review

# Global configuration
MODEL_NAME = "paraphrase-MiniLM-L3-v2" 
BATCH_SIZE = 8  
SIMILARITY_THRESHOLD = 0.2  
MAX_RESULTS = 20 
N_TOPICS = 15  
MIN_CLUSTER_SIZE = 3  
DEFAULT_N_SIMILAR = 10  

# Model singleton to avoid reloading
_model = None

def get_model() -> SentenceTransformer:
    """Singleton pattern for embedding model to avoid reloading."""
    global _model
    if _model is None:
        # Force CPU usage and disable tokenizer parallelism to reduce memory spikes
        import os
        os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
        _model = SentenceTransformer(MODEL_NAME, device='cpu')
    return _model

def process_in_batches(items: List[Any], batch_size: int = BATCH_SIZE):
    """Process a list in batches to manage memory usage."""
    for i in range(0, len(items), batch_size):
        yield items[i:i + batch_size]

def precompute_embeddings(db: Session) -> bool:
    """Precompute embeddings for all reviews using batched processing."""
    model = get_model()
    reviews = db.query(Review).filter(Review.text.isnot(None), Review.embedding.is_(None)).all()
    
    print(f"[Embeddings] Processing {len(reviews)} reviews in batches of {BATCH_SIZE}...")
    processed = 0
    
    for batch in process_in_batches(reviews, BATCH_SIZE):
        texts = [preprocess_review(r.text, r.name) for r in batch]
        try:
            embeddings = model.encode(texts, batch_size=BATCH_SIZE, 
                                    show_progress_bar=False, 
                                    convert_to_numpy=True, 
                                    device='cpu')
            for review, embedding in zip(batch, embeddings):
                review.embedding = json.dumps(embedding.tolist())
            
        except Exception as e:
            print(f"[Embeddings] Error batch encoding: {e}. Trying one-by-one...")
            for review, txt in zip(batch, texts):
                try:
                    emb = model.encode(txt, show_progress_bar=False, 
                                     convert_to_numpy=True, device='cpu')
                    review.embedding = json.dumps(emb.tolist())
                except Exception as e2:
                    print(f"[Embeddings] Error encoding review {review.id}: {e2}")
                    continue
        
        db.commit()
        processed += len(batch)
        print(f"[Embeddings] {processed}/{len(reviews)} reviews processed")

    print("[Embeddings] Process completed")
    return True

def find_similar_to_query(db: Session, query: str, 
                         neighborhood: Optional[str] = None,
                         min_rating: float = 0.0, 
                         n_similar: int = MAX_RESULTS) -> List[Dict]:
    """Find places similar to a query using embeddings."""
    print(f"[Search] Starting search - Query: '{query}', Neighborhood: '{neighborhood}', Min rating: {min_rating}")
    
    # Filter reviews
    query_obj = db.query(Review).filter(Review.embedding.isnot(None))
    
    # If no query, show highest rated
    if not query or query.strip() == "":
        query_obj = query_obj.order_by(Review.rating.desc())
    
    if neighborhood and neighborhood != "Todos":
        query_obj = query_obj.filter(Review.name.ilike(f"%{neighborhood}%"))
    if min_rating > 0:
        query_obj = query_obj.filter(Review.rating >= min_rating)
    
    reviews = query_obj.all()
    print(f"[Search] Found {len(reviews)} reviews matching filters")
    
    if not reviews:
        return []

    # If no query, return highest rated
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

    # Generate query embedding
    model = get_model()
    query_embedding = model.encode(preprocess_review(query))
    print("[Search] Query embedding generated")
    
    # Calculate similarities in batches
    results = []
    for batch in process_in_batches(reviews):
        batch_embeddings = np.array([np.array(json.loads(r.embedding)) for r in batch])
        similarities = cosine_similarity([query_embedding], batch_embeddings)[0]
        
        for i, (review, similarity) in enumerate(zip(batch, similarities)):
            if similarity > SIMILARITY_THRESHOLD:
                # Combine similarity with rating for better ranking
                rating = float(review.rating) if review.rating else 0.0
                rating_norm = rating / 5.0  # normalize to [0,1]
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
    
    # Sort by combined score or similarity
    results.sort(key=lambda x: x.get("score", x.get("similarity_score", 0.0)), 
                reverse=True)
    return results[:n_similar]

def get_similar_reviews(db: Session, review_id: int, 
                       n: int = DEFAULT_N_SIMILAR) -> List[Dict]:
    """Find reviews similar to a given review."""
    source = db.query(Review).filter(Review.id == review_id).first()
    if not source or not source.embedding:
        return []

    # Get reviews with embeddings excluding source
    reviews = db.query(Review).filter(
        Review.embedding.isnot(None),
        Review.id != review_id
    ).all()
    if not reviews:
        return []

    # Calculate similarities
    source_embedding = np.array(json.loads(source.embedding))
    results = []
    
    for batch in process_in_batches(reviews):
        batch_embeddings = np.array([np.array(json.loads(r.embedding)) 
                                   for r in batch])
        similarities = cosine_similarity([source_embedding], batch_embeddings)[0]
        
        for review, sim in zip(batch, similarities):
            if sim > SIMILARITY_THRESHOLD:
                results.append({
                    "review": review,
                    "similarity": float(sim)
                })
    
    # Sort by similarity and return top N
    results.sort(key=lambda x: x["similarity"], reverse=True)
    return [(r["review"], r["similarity"]) for r in results[:n]]

def run_topic_modeling(db: Session, n_topics: int = N_TOPICS) -> bool:
    """Group reviews into topics using KMeans clustering over embeddings."""
    print(f"[TopicModeling] Starting with {n_topics} topics...")
    
    # Ensure all reviews have embeddings
    missing_count = db.query(Review).filter(
        Review.text.isnot(None), 
        Review.embedding.is_(None)
    ).count()
    
    if missing_count > 0:
        print(f"[TopicModeling] Found {missing_count} reviews without embeddings. Precomputing...")
        precompute_embeddings(db)

    # Get reviews with embeddings
    reviews = db.query(Review).filter(Review.embedding.isnot(None)).all()
    if not reviews:
        print("[TopicModeling] No reviews with embeddings to process")
        return False

    # Adjust number of topics based on data size
    if len(reviews) < n_topics * MIN_CLUSTER_SIZE:
        adjusted_topics = max(2, len(reviews) // MIN_CLUSTER_SIZE)
        print(f"[TopicModeling] Adjusting topics to {adjusted_topics} due to data size")
        n_topics = adjusted_topics

    # Convert embeddings to numpy matrix
    embeddings = np.array([np.array(json.loads(r.embedding)) for r in reviews])
    
    # Apply KMeans
    kmeans = KMeans(n_clusters=n_topics, random_state=42, n_init=10, max_iter=300)
    labels = kmeans.fit_predict(embeddings)
    
    # Find representative words per cluster
    cluster_texts = [[] for _ in range(n_topics)]
    cluster_sizes = [0] * n_topics
    for i, review in enumerate(reviews):
        cluster_texts[labels[i]].append(
            preprocess_review(review.text, review.name)
        )
        cluster_sizes[labels[i]] += 1
    
    print("\nCluster distribution:")
    for i, size in enumerate(cluster_sizes):
        print(f"Cluster {i}: {size} reviews")
    
    # Assign topics and update H3 indices
    processed = 0
    for batch_start in range(0, len(reviews), BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, len(reviews))
        batch = reviews[batch_start:batch_end]
        batch_labels = labels[batch_start:batch_end]
        
        for review, label in zip(batch, batch_labels):
            # Get most significant words from cluster
            texts_in_cluster = ' '.join(cluster_texts[label])
            words = texts_in_cluster.split()
            
            # Calculate simplified TF-IDF
            word_freq = {}
            for word in set(words):
                # TF: frequency in this cluster
                tf = words.count(word)
                # IDF: penalize words common across clusters
                other_clusters_with_word = sum(
                    1 for i in range(n_topics) 
                    if i != label and word in ' '.join(cluster_texts[i])
                )
                significance = tf * (1.0 / (1.0 + other_clusters_with_word))
                word_freq[word] = significance
            
            # Select most significant words
            significant_words = sorted(word_freq.items(), key=lambda x: -x[1])[:4]
            selected_words = [w for w, _ in significant_words]
            
            # Update review
            review.topic = f"Topic {label}: {', '.join(selected_words)}"
            
            # Update H3 index if coordinates available
            if review.lat is not None and review.lon is not None:
                try:
                    review.h3_index = h3.geo_to_h3(
                        float(review.lat), float(review.lon), 7
                    )
                except Exception as e:
                    print(f"Error computing H3 for review {review.id}: {e}")
                    review.h3_index = None
            
            processed += 1
        
        db.commit()
        print(f"[TopicModeling] {processed}/{len(reviews)} reviews processed")
    
    print("[TopicModeling] Process completed")
    return True
    

