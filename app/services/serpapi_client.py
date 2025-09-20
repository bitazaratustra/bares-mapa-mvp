import requests
import os
from dotenv import load_dotenv

load_dotenv()
SERPAPI_KEY = os.getenv("SERPAPI_KEY")

def get_place_reviews(place_id: str):
    params = {
        "engine": "google_maps_reviews",
        "place_id": place_id,
        "api_key": SERPAPI_KEY
    }
    try:
        response = requests.get("https://serpapi.com/search", params=params, timeout=10)
        data = response.json()
        return data.get("reviews", [])
    except Exception as e:
        print(f"[Error] get_place_reviews: {e}")
        return []

def get_reviews_google_maps(query: str, location: str, num: int = 10):
    """Devuelve lista de reseñas de Google Maps filtradas por CABA"""
    reviews_list = []
    params = {
        "engine": "google_maps",
        "q": query,
        "location": location,
        "google_domain": "google.com.ar",
        "gl": "ar",
        "hl": "es",
        "api_key": SERPAPI_KEY
    }
    
    try:
        response = requests.get("https://serpapi.com/search", params=params, timeout=15)
        data = response.json()
        
        if not data.get("local_results"):
            return []
            
        for place in data.get("local_results", [])[:num]:
            place_id = place.get("place_id")
            name = place.get("title")
            lat = place.get("gps_coordinates", {}).get("latitude")
            lon = place.get("gps_coordinates", {}).get("longitude")
            
            # Filtro estricto por coordenadas de CABA
            if lat and lon:
                # Coordenadas aproximadas de CABA
                caba_bounds = {
                    "min_lat": -34.70, "max_lat": -34.53,
                    "min_lon": -58.53, "max_lon": -58.34
                }
                
                if (caba_bounds["min_lat"] <= lat <= caba_bounds["max_lat"] and
                    caba_bounds["min_lon"] <= lon <= caba_bounds["max_lon"]):
                    
                    reviews = get_place_reviews(place_id)
                    for r in reviews:
                        reviews_list.append({
                            "place_id": place_id,
                            "name": name,
                            "lat": lat,
                            "lon": lon,
                            "text": r.get("snippet"),
                            "rating": r.get("rating"),
                            "source": "Google Maps"
                        })
    
    except Exception as e:
        print(f"[Error] Error en la búsqueda: {str(e)}")
    
    return reviews_list