from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.init_db import Review
from collections import defaultdict

router = APIRouter()

@router.get("/")
def get_reviews_map(
    db: Session = Depends(get_db),
    topic_filter: str = Query(None, description="Filtrar por topic")
):
    query = db.query(Review)
    if topic_filter:
        query = query.filter(Review.topic == topic_filter)

    reviews = query.all()
    map_data = defaultdict(list)
    for r in reviews:
        if r.h3_index:
            map_data[r.h3_index].append({
                "name": r.name,
                "text": r.text,
                "rating": r.rating,
                "topic": r.topic,
                "lat": r.lat,
                "lon": r.lon
            })

    return dict(map_data)