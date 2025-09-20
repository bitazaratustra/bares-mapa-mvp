from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db

router = APIRouter()

@router.get("/neighborhoods")
def get_neighborhoods():
    """Obtener lista de barrios únicos de Buenos Aires"""
    BARRIOS = [
        "Todos", "Palermo", "Recoleta", "San Telmo", "Belgrano", "Caballito",
        "Villa Crespo", "Almagro", "Puerto Madero", "San Nicolás",
        "Monserrat", "Villa Urquiza", "Núñez", "Colegiales", "Chacarita",
        "Villa Ortúzar", "Boedo", "Barracas", "La Boca", "Flores"
    ]
    return BARRIOS