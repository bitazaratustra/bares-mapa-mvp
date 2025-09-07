from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.database import get_db
from app.db.init_db import Review
from app.services.scrape_utils import scrape_and_save_reviews

router = APIRouter()

@router.get("/scrape")
def scrape_reviews(
    query: str = "bares palermo", 
    location: str = "Palermo, CABA", 
    db: Session = Depends(get_db)
):
    scraped = scrape_and_save_reviews(db, query=query, location=location)
    return {"scraped": scraped}

@router.get("/reviews_json")
async def get_reviews_json(db: Session = Depends(get_db)):
    try:
        # Primero intentamos leer de la base de datos
        reviews = db.query(Review).all()
        if reviews:
            return [
                {
                    "id": r.id,
                    "name": r.name,
                    "lat": float(r.lat) if r.lat else None,
                    "lon": float(r.lon) if r.lon else None,
                    "rating": float(r.rating) if r.rating else None,
                    "text": r.text,
                    "topic": r.topic,
                    "category": r.category
                }
                for r in reviews
            ]
        
        # Si no hay datos en la DB, intentamos leer del archivo JSON
        with open("app/static/reviews.json", "r", encoding="utf-8") as f:
            content = f.read()
            print(f"Leyendo reviews.json: {len(content)} bytes")
            return Response(content=content, media_type="application/json")
    except FileNotFoundError:
        print("¡Archivo reviews.json no encontrado!")
        return []
    except Exception as e:
        print(f"Error leyendo reviews: {str(e)}")
        return []

@router.get("/stats")
def get_review_stats(db: Session = Depends(get_db)):
    total_reviews = db.query(Review).count()
    total_topics = db.query(Review.topic).distinct().count()
    avg_rating = db.query(func.avg(Review.rating)).scalar() or 0
    
    return {
        "total_reviews": total_reviews,
        "total_topics": total_topics,
        "avg_rating": float(avg_rating)
    }