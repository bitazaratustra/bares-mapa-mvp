from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.init_db import Review
from app.services.topic_model import run_topic_modeling, find_similar_places
from typing import List, Dict
from pydantic import BaseModel

router = APIRouter()

class SearchRequest(BaseModel):
    neighborhood: str
    topic: str

@router.post("/search")
def search_places(request: SearchRequest, db: Session = Depends(get_db)):
    """
    Busca lugares según el barrio y el tópico seleccionado
    """
    try:
        # Filtrar por barrio
        reviews = db.query(Review).filter(
            Review.name.ilike(f"%{request.neighborhood}%")
        ).all()
        
        if not reviews:
            return []
            
        # Usar BERTopic para encontrar lugares similares basados en el tópico
        results = find_similar_places(reviews, request.topic, db)
        return results
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error en la búsqueda: {str(e)}"
        )

@router.post("/run_topic_modeling")
def run_topic_modeling_endpoint(db: Session = Depends(get_db)):
    try:
        topic_model = run_topic_modeling(db)
        if topic_model:
            return {"message": "Topic modeling completado exitosamente"}
        else:
            return {"message": "No se pudo completar el topic modeling"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error ejecutando topic modeling: {str(e)}"
        )

@router.get("/topics")
def get_topics(db: Session = Depends(get_db)):
    """Retorna la lista de tópicos disponibles"""
    try:
        # Obtener tópicos únicos de la base de datos
        topics = db.query(Review.topic).distinct().filter(Review.topic.isnot(None)).all()
        topics_dict = {}
        for i, (topic,) in enumerate(topics):
            if topic:
                # Limpiar el topic (por si viene con caracteres especiales)
                clean_topic = topic.strip()
                if clean_topic:
                    topics_dict[str(i)] = clean_topic
        return topics_dict
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo tópicos: {str(e)}"
        )

@router.get("/similar/{place_id}")
def get_similar_places_endpoint(
    place_id: str,
    db: Session = Depends(get_db)
) -> List[Dict]:
    """
    Retorna lugares similares para un lugar específico
    """
    try:
        reviews = db.query(Review).filter(Review.text != None).all()
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
