from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Index
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Review(Base):
    __tablename__ = "reviews"
    id = Column(Integer, primary_key=True)
    place_id = Column(String, nullable=False)
    name = Column(String)
    lat = Column(Float)
    lon = Column(Float)
    category = Column(String)
    rating = Column(Float)
    text = Column(Text)
    language = Column(String)
    created_at = Column(DateTime)
    source = Column(String)
    topic = Column(String)
    h3_index = Column(String)
    embedding = Column(Text)  # Almacenado como texto JSON

    # Índices para optimizar búsquedas
    __table_args__ = (
        Index('idx_reviews_neighborhood', 'name'),
        Index('idx_reviews_rating', 'rating'),
        Index('idx_reviews_topic', 'topic'),
    )

DATABASE_URL = "postgresql+psycopg2://esteban:1234@localhost:5432/bares_db"
engine = create_engine(DATABASE_URL)

def init_db():
    Base.metadata.create_all(engine)
    print("Tablas creadas correctamente.")

if __name__ == "__main__":
    init_db()
