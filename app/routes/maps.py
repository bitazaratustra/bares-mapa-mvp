from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.init_db import Review
from collections import defaultdict

router = APIRouter()

@router.get("/")
def get_reviews_map(
    db: Session = Depends(get_db),
    topic_filter: int | None = Query(None, description="Filtrar por topic"),
    rating_filter: float | None = Query(None, description="Filtrar por rating mínimo"),
):
    query = db.query(Review)
    if topic_filter is not None:
        query = query.filter(Review.topic == topic_filter)
    if rating_filter is not None:
        query = query.filter(Review.rating >= rating_filter)

    reviews = query.all()
    map_data = defaultdict(list)
    for r in reviews:
        if r.h3_index:
            map_data[r.h3_index].append(
                {
                    "name": r.name,
                    "text": r.text,
                    "rating": r.rating,
                    "topic": r.topic,
                    "lat": float(r.lat) if r.lat else None,
                    "lon": float(r.lon) if r.lon else None,
                }
            )

    return dict(map_data)