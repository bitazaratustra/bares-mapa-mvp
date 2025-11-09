# precompute_embeddings.py
from app.db.database import get_db
from app.services.topic_model import precompute_embeddings

if __name__ == "__main__":
    db = next(get_db())
    precompute_embeddings(db)
    print("Embeddings precomputation completed")