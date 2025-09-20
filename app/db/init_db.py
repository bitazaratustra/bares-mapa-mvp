from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Review(Base):
    __tablename__ = "reviews"
    id = Column(Integer, primary_key=True, autoincrement=True)
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
    topic = Column(Integer, nullable=True)
    h3_index = Column(String, nullable=True)
    embedding = Column(Text)

DATABASE_URL = "postgresql+psycopg2://esteban:1234@localhost:5432/bares_db"
engine = create_engine(DATABASE_URL)

def init_db():
    Base.metadata.create_all(engine)
    print("Tablas creadas correctamente.")

if __name__ == "__main__":
    init_db()