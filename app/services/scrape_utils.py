from app.db.init_db import Review
from app.services.serpapi_client import get_reviews_google_maps
from app.services.export_reviews import export_reviews_json

def scrape_and_save_reviews(db, query="bares", location="Buenos Aires", num=5):
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
    db.commit()
    export_reviews_json(db)
    return scraped

def main():
    from app.db.database import get_db
    db = next(get_db())
    scraped = scrape_and_save_reviews(db)
    print(f"Reseñas guardadas: {scraped}")

if __name__ == "__main__":
    main()