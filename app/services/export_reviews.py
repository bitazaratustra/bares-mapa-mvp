import json
from app.db.init_db import Review

def export_reviews_json(db):
    reviews = db.query(Review).all()
    data = []
    for r in reviews:
        data.append({
            "name": r.name,
            "text": r.text,
            "lat": r.lat,
            "lon": r.lon,
            "rating": r.rating,
            "topic": r.topic,
            "h3_index": r.h3_index
        })
    with open("app/static/reviews.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
