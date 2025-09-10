from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
from sqlalchemy import distinct
from app.db.database import get_db
from app.db.init_db import Review
from app.services.scrape_utils import scrape_and_save_reviews

router = APIRouter()

@router.get("/neighborhoods")
def get_neighborhoods(db: Session = Depends(get_db)):
    """Obtener lista de barrios únicos"""
    try:
        # Extraer nombres de barrios de los nombres de lugares
        neighborhoods = db.query(distinct(Review.name)).all()
        unique_neighborhoods = set()
        
        for (name,) in neighborhoods:
            # Buscar el nombre del barrio en el nombre del lugar
            barrios = ["Palermo", "Recoleta", "San Telmo", "Belgrano", "Caballito", 
                      "Villa Crespo", "Almagro", "Puerto Madero", "San Nicolás", 
                      "Monserrat", "Villa Urquiza", "Núñez", "Colegiales", "Chacarita",
                      "Villa Ortúzar", "Boedo", "Barracas", "La Boca", "Flores"]
            
            for barrio in barrios:
                if barrio.lower() in name.lower():
                    unique_neighborhoods.add(barrio)
                    break
        
        return sorted(list(unique_neighborhoods))
    except Exception as e:
        print(f"Error obteniendo barrios: {str(e)}")
        return []

@router.get("/scrape")
def scrape_reviews(
    query: str = "bares palermo", 
    location: str = "Palermo, CABA", 
    db: Session = Depends(get_db)
):
    scraped = scrape_and_save_reviews(db, query=query, location=location, num=10)
    return {"scraped": scraped}

@router.get("/reviews_json")
async def get_reviews_json(db: Session = Depends(get_db)):
    from app.db.init_db import Review
    import json
    
    try:
        # Obtener reviews de la base de datos
        reviews = db.query(Review).all()
        reviews_list = []
        
        for review in reviews:
            reviews_list.append({
                "id": review.id,
                "place_id": review.place_id,
                "name": review.name,
                "lat": float(review.lat) if review.lat else None,
                "lon": float(review.lon) if review.lon else None,
                "text": review.text,
                "rating": float(review.rating) if review.rating else None,
                "topic": review.topic,
                "h3_index": review.h3_index
            })
        
        # Guardar en archivo para cache
        with open("app/static/reviews.json", "w", encoding="utf-8") as f:
            json.dump(reviews_list, f, ensure_ascii=False, indent=2)
        
        return reviews_list
    except Exception as e:
        print(f"Error obteniendo reviews: {str(e)}")
        return []
