from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Index

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
    embedding = Column(Text)  

    
    __table_args__ = (
        Index('idx_reviews_neighborhood', 'name'),
        Index('idx_reviews_rating', 'rating'),
        Index('idx_reviews_topic', 'topic'),
    )
