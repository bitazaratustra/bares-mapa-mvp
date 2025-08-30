from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services.scrape_utils import scrape_and_save_reviews

router = APIRouter()

@router.get("/scrape")
def scrape_reviews(
    query: str = "bares palermo", 
    location: str = "Palermo, CABA", 
    db: Session = Depends(get_db)
):
    scraped = scrape_and_save_reviews(db, query=query, location=location, num=10)
    return {"scraped": scraped}

@router.get("/reviews_json")
async def get_reviews_json():
    try:
        with open("app/static/reviews.json", "r", encoding="utf-8") as f:
            content = f.read()
            print(f"Leyendo reviews.json: {len(content)} bytes")
            return Response(content=content, media_type="application/json")
    except FileNotFoundError:
        print("¡Archivo reviews.json no encontrado!")
        return []
    except Exception as e:
        print(f"Error leyendo reviews.json: {str(e)}")
        return []
