from app.models.review import Review
from app.db.database import get_db
from app.services.serpapi_client import get_reviews_google_maps
from app.services.export_reviews import export_reviews_json

def scrape_and_save_reviews(db, query="pub", location="Buenos Aires", num: int = 50):
    print(f"[Scraping] Iniciando scraping con num={num}")
    reviews = get_reviews_google_maps(query, location, num)
    scraped = 0
    for r in reviews:
        try:
            place_id = r.get("place_id")
            text = r.get("text")

            # Deduplicar por place_id + texto (si existe exactamente igual)
            exists = db.query(Review).filter(
                Review.place_id == place_id,
                Review.text == text
            ).first() if place_id else None

            if exists:
                print(f"[Scraping] Saltando reseña duplicada para place_id={place_id}")
                continue

            review_obj = Review(
                place_id=place_id,
                name=r.get("name"),
                lat=r.get("lat"),
                lon=r.get("lon"),
                text=text,
                rating=r.get("rating"),
                source=r.get("source"),
            )
            db.add(review_obj)
            scraped += 1
            if scraped % 5 == 0:
                db.commit()  # Commit cada 5 para liberar memoria
                print(f"[Scraping] {scraped} reseñas guardadas...")
        except Exception as e:
            print(f"[Scraping] Error guardando reseña: {e}")
            db.rollback()
            continue
    db.commit()
    export_reviews_json(db)
    print(f"[Scraping] Proceso finalizado. Total: {scraped}")
    return scraped

def main():
    db = next(get_db())
    scraped = scrape_and_save_reviews(db)
    print(f"Reseñas guardadas: {scraped}")

if __name__ == "__main__":
    main()
