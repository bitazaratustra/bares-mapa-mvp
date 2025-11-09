from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.review import Review
from app.services.topic_model import run_topic_modeling, find_similar_to_query
from typing import Optional, List, Dict
from pydantic import BaseModel

router = APIRouter()

class SearchRequest(BaseModel):
    neighborhood: Optional[str] = None
    topic: Optional[str] = None
    query: Optional[str] = None
    min_rating: Optional[float] = None

@router.post("/search")
def search_places(request: SearchRequest, db: Session = Depends(get_db)):
    """
    Busca lugares según el barrio y el tópico seleccionado
    """
    try:
        # Preparar la consulta base
        query = request.query or request.topic or ""
        neighborhood = request.neighborhood if request.neighborhood and request.neighborhood != "Todos" else None
        min_rating = request.min_rating if request.min_rating else 0.0
        
        # Usar la función de búsqueda semántica
        results = find_similar_to_query(
            db=db,
            query=query,
            neighborhood=neighborhood,
            min_rating=min_rating
        )
        
        return results
        
    except Exception as e:
        print(f"Error en búsqueda: {str(e)}")  # Log para debugging
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

@router.get("/similar/{review_id}")
def get_similar_places_endpoint(
    review_id: int,
    db: Session = Depends(get_db)
) -> List[Dict]:
    """
    Retorna lugares similares para un lugar específico basado en su ID
    """
    try:
        from app.services.topic_model import get_similar_reviews
        
        similar_places = get_similar_reviews(db, review_id)
        
        if not similar_places:
            return []
            
        results = []
        for review, similarity in similar_places:
            results.append({
                "place_id": review.place_id,
                "name": review.name,
                "lat": float(review.lat) if review.lat else None,
                "lon": float(review.lon) if review.lon else None,
                "rating": float(review.rating) if review.rating else None,
                "text": review.text,
                "topic": review.topic,
                "similarity_score": float(similarity)
            })
            
        return results
        
    except Exception as e:
        print(f"Error obteniendo lugares similares: {str(e)}")  # Log para debugging
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo lugares similares: {str(e)}"
        )
        