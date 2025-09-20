# precompute_embeddings.py
from db.database import get_db
from services.topic_model_utils import precompute_embeddings

if __name__ == "__main__":
    db = next(get_db())
    precompute_embeddings(db)
    print("Embeddings precomputation completed")