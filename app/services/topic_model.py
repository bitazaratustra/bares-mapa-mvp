from sqlalchemy.orm import Session
from app.db.database import get_db
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
    reviews = db.query(Review).filter(Review.text != None).all()
    texts = [preprocess(r.text) for r in reviews]
    ids = [r.id for r in reviews]

    model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    embeddings = model.encode(texts, show_progress_bar=True)

    topic_model = BERTopic(language="multilingual")
    topics, _ = topic_model.fit_transform(texts, embeddings)

    for idx, r in enumerate(reviews):
        r.topic = str(topics[idx])
        if r.lat and r.lon:
            r.h3_index = h3.geo_to_h3(r.lat, r.lon, 7)

    db.commit()
    print(f"Topics y H3 asignados a {len(reviews)} reseñas.")
    return topic_model
