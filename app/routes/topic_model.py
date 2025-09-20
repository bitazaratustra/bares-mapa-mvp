from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.init_db import Review
from app.services.topic_model_utils import find_similar_to_query
from typing import List
from pydantic import BaseModel

router = APIRouter()

class SearchRequest(BaseModel):
    neighborhood: str
    query: str
    min_rating: float = 4.0

@router.post("/search")
def search_places(request: SearchRequest, db: Session = Depends(get_db)):
    try:
        # Add timeout protection
        results = find_similar_to_query(
            db, 
            request.query, 
            request.neighborhood, 
            request.min_rating
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/run_topic_modeling")
def run_topic_modeling_endpoint(db: Session = Depends(get_db)):
    try:
        from app.services.topic_model_utils import run_topic_modeling
        topic_model = run_topic_modeling(db)
        if topic_model:
            return {"message": "Topic modeling completado exitosamente"}
        else:
            return {"message": "No se pudo completar el topic modeling"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/topics")
def get_topics(db: Session = Depends(get_db)):
    """Retorna la lista de tópicos disponibles"""
    try:
        topics = db.query(Review.topic).distinct().filter(Review.topic.isnot(None)).all()
        topics_list = [topic[0] for topic in topics if topic[0]]
        return topics_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))