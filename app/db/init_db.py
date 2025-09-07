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
    topic = Column(String, nullable=True)  # Changed to String as per DB schema
    h3_index = Column(String, nullable=True)

DATABASE_URL = "postgresql+psycopg2://esteban:1234@localhost:5432/bares_db"

def init_db():
    try:
        # Primero intenta crear la base de datos si no existe
        temp_engine = create_engine('postgresql+psycopg2://esteban:1234@localhost:5432/postgres')
        conn = temp_engine.connect()
        conn.execute("commit")
        conn.execute("create database bares_db")
        conn.close()
        print("Base de datos creada correctamente.")
    except Exception as e:
        print(f"La base de datos ya existe o hubo un error: {str(e)}")

    # Crea las tablas
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
    print("Tablas creadas correctamente.")
    return engine

if __name__ == "__main__":
    init_db()