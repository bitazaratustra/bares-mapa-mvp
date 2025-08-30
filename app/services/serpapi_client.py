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
    """Devuelve lista de reseñas de Google Maps via SerpApi"""
    reviews_list = []
    params = {
        "engine": "google_maps",
        "q": f"{query} CABA",  # Forzar búsqueda en CABA
        "type": "search",
        "location": "Buenos Aires, Argentina",
        "google_domain": "google.com.ar",  # Usar Google Argentina
        "gl": "ar",  # Región Argentina
        "hl": "es",  # Idioma español
        "ll": "@-34.6037,-58.3816,13z",  # Centro en Buenos Aires
        "api_key": SERPAPI_KEY
    }
    
    print(f"[Info] Buscando '{query}' en '{location}'")
    try:
        response = requests.get("https://serpapi.com/search", params=params)
        print(f"[Debug] Status Code: {response.status_code}")
        data = response.json()
        print(f"[Debug] Resultados encontrados: {len(data.get('local_results', []))}")
    except Exception as e:
        print(f"[Error] Error en la búsqueda: {str(e)}")
        return []

    if not data.get("local_results"):
        print("[Error] No se encontraron resultados locales")
        return []

    for place in data.get("local_results", [])[:num]:
        place_id = place.get("place_id")
        name = place.get("title")
        lat = place.get("gps_coordinates", {}).get("latitude")
        lon = place.get("gps_coordinates", {}).get("longitude")
        
        # Coordenadas aproximadas de Buenos Aires
        if lat and lon:
            print(f"[Debug] Lugar encontrado: {name} en {lat}, {lon}")
            # Rango más amplio que cubre toda CABA
            # Límites de CABA (aprox)
            lat_min, lat_max = -34.7, -34.5  # Latitud: de Constitución a Núñez
            lon_min, lon_max = -58.5, -58.3  # Longitud: de Liniers a Puerto Madero
            
            if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
                print(f"[Debug] ✓ {name} está dentro de CABA")
            else:
                print(f"[Debug] Descartando {name} - fuera de Buenos Aires")
                continue

        try:
            reviews = get_place_reviews(place_id)
            print(f"[Debug] Reseñas encontradas para {name}: {len(reviews)}")
            for r in reviews:
                reviews_list.append({
                    "place_id": place_id,
                    "name": name,
                    "lat": lat,
                    "lon": lon,
                    "text": r.get("snippet"),
                    "rating": r.get("rating"),
                    "created_at": r.get("time"),
                    "source": "Google Maps"
                })
        except Exception as e:
            print(f"[Error] Error obteniendo reseñas para {name}: {str(e)}")
            continue
    
    print(f"[Info] Se encontraron {len(reviews_list)} reseñas en total")
    return reviews_list
    print(f"[Info] Buscando '{query}' en '{location}'")
    response = requests.get("https://serpapi.com/search", params=params)
    data = response.json()

    if not data.get("local_results"):
        print("[Error] No se encontraron resultados locales")
        return []

    for place in data.get("local_results", [])[:num]:
        place_id = place.get("place_id")
        name = place.get("title")
        lat = place.get("gps_coordinates", {}).get("latitude")
        lon = place.get("gps_coordinates", {}).get("longitude")
        
        if lat and lon and -35 > lat > -34 and -59 > lon > -58:  # Filtro para Buenos Aires
            reviews = get_place_reviews(place_id)
            for r in reviews:
                reviews_list.append({
                    "place_id": place_id,
                    "name": name,
                    "lat": lat,
                    "lon": lon,
                    "text": r.get("snippet"),
                    "rating": r.get("rating"),
                    "created_at": r.get("time"),
                    "source": "Google Maps"
                })
    
    print(f"[Info] Se encontraron {len(reviews_list)} reseñas")
    return reviews_list
