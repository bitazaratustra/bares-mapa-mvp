from sqlalchemy.orm import Session
from app.db.init_db import Review
from sentence_transformers import SentenceTransformer
from bertopic import BERTopic
import h3
import re
import nltk

nltk.download("stopwords")
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
    reviews = db.query(Review).filter(Review.text.isnot(None)).all()
    if not reviews:
        print("No hay reseñas para procesar.")
        return None

    texts = [preprocess(r.text) for r in reviews]

    model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    embeddings = model.encode(texts, show_progress_bar=True)

    topic_model = BERTopic(language="multilingual")
    topics, _ = topic_model.fit_transform(texts, embeddings)

    updated = 0
    for idx, r in enumerate(reviews):
        topic_val = topics[idx]
        r.topic = None if topic_val == -1 else int(topic_val)

        if r.lat is not None and r.lon is not None:
            try:
                r.h3_index = h3.geo_to_h3(float(r.lat), float(r.lon), 7)
            except Exception as e:
                print(f"Error calculando H3 para review {r.id}: {e}")
        updated += 1

    db.commit()
    print(f"Topics y H3 asignados a {updated} reseñas.")
    return topic_model
