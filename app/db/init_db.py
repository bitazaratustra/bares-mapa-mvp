from app.models.review import Base
from app.db.database import engine
from app.services.topic_model import precompute_embeddings, run_topic_modeling
from app.db.database import get_db

def init_db():
    """Initialize database schema and compute initial embeddings/topics."""
    # Create tables
    Base.metadata.create_all(engine)
    print("Tables created successfully.")
    
    # Initialize data if needed
    try:
        db = next(get_db())
        precompute_embeddings(db)
        run_topic_modeling(db)
        print("Initial embeddings and topics computed.")
    except Exception as e:
        print(f"Warning: Could not compute initial embeddings/topics: {e}")

if __name__ == "__main__":
    init_db()
