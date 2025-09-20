from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text

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
    topic = Column(String, nullable=True)
    h3_index = Column(String, nullable=True)