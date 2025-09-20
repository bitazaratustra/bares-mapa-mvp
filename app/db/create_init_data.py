# create_init_data.py
from app.db.database import get_db
from app.services.topic_model_utils import precompute_embeddings, run_topic_modeling

def initialize_data():
    db = next(get_db())
    run_topic_modeling(db)
    precompute_embeddings(db)
    print("Data initialization complete")

if __name__ == "__main__":
    initialize_data()