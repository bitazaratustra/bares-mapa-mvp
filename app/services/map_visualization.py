import folium
from app.db.init_db import Review
from sqlalchemy.orm import Session

def create_reviews_map(db: Session, center_lat=-34.6037, center_lon=-58.3816, zoom_start=12):
    reviews = db.query(Review).all()
    m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom_start)
    for r in reviews:
        if r.lat and r.lon:
            folium.Marker(
                location=[float(r.lat), float(r.lon)],
                popup=f"<b>{r.name}</b><br>Rating: {r.rating}<br>{r.text}<br>Topic: {r.topic}",
                tooltip=r.name,
            ).add_to(m)
    return m

def save_map_html(db: Session, filepath="app/static/reviews_map.html"):
    m = create_reviews_map(db)
    m.save(filepath)
