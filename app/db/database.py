from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Database configuration
DATABASE_URL = "postgresql+psycopg2://esteban:1234@localhost:5432/bares_db"

# Create engine instance
engine = create_engine(DATABASE_URL)

# Configure session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()