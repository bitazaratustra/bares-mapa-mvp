import folium
import pandas as pd
from app.db.init_db import Review
from sqlalchemy.orm import Session
from app.db.database import get_db

# Función para crear un mapa con reseñas

def create_reviews_map(db: Session, center_lat=-34.6037, center_lon=-58.3816, zoom_start=12):
    reviews = db.query(Review).all()
    m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom_start)
    for r in reviews:
        folium.Marker(
            location=[r.lat, r.lon],
            popup=f"<b>{r.name}</b><br>Rating: {r.rating}<br>{r.text}",
            tooltip=r.name
        ).add_to(m)
    return m

# Guardar el mapa como HTML

def save_map_html(db: Session, filepath="data/reviews_map.html"):
    m = create_reviews_map(db)
    m.save(filepath)
