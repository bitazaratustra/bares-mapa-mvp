from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.init_db import Review
from app.services.topic_model import run_topic_modeling, find_similar_places, TOPIC_KEYWORDS
from typing import List, Dict

router = APIRouter()

@router.post("/run_topic_modeling")
def run_topic_modeling_endpoint(db: Session = Depends(get_db)):
    try:
        result = run_topic_modeling(db)
        if result:
            return {"message": "Topic modeling completado exitosamente"}
        else:
            return {"message": "No se pudo completar el topic modeling"}
    except Exception as e:
        return {"error": f"Error ejecutando topic modeling: {str(e)}"}

@router.get("/topics")
def get_topics():
    """Retorna la lista de tópicos disponibles"""
    return {i: topic for i, topic in enumerate(TOPIC_KEYWORDS.keys())}

@router.get("/similar/{place_id}")
def get_similar_places_endpoint(
    place_id: str,
    db: Session = Depends(get_db)
) -> List[Dict]:
    """
    Retorna lugares similares para un lugar específico
    """
    try:
        reviews = db.query(Review).filter(Review.text.isnot(None)).all()
        target_review = db.query(Review).filter(Review.place_id == place_id).first()
        
        if not target_review:
            raise HTTPException(status_code=404, detail="Lugar no encontrado")
        
        return find_similar_places(reviews, target_review)
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo lugares similares: {str(e)}"
        )