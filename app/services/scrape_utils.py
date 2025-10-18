from app.db.init_db import Review
from app.db.database import get_db
from app.services.serpapi_client import get_reviews_google_maps
from app.services.export_reviews import export_reviews_json

def scrape_and_save_reviews(db, query="cervecería buenos aires", location="Buenos Aires", num=15):
    print(f"[Scraping] Iniciando scraping con num={num}")
    reviews = get_reviews_google_maps(query, location, num)
    scraped = 0
    for r in reviews:
        review_obj = Review(
            place_id=r["place_id"],
            name=r["name"],
            lat=r["lat"],
            lon=r["lon"],
            text=r["text"],
            rating=r["rating"],
            source=r.get("source"),
        )
        db.add(review_obj)
        scraped += 1
        if scraped % 5 == 0:
            db.commit()  # Commit cada 5 para liberar memoria
            print(f"[Scraping] {scraped} reseñas guardadas...")
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
