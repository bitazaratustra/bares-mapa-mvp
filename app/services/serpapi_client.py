import requests
import os
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import List, Dict, Any

load_dotenv()
SERPAPI_KEY = os.getenv("SERPAPI_KEY")


def _check_api_key() -> bool:
    if not SERPAPI_KEY:
        print("[SerpAPI] ERROR: SERPAPI_KEY not set. Please add SERPAPI_KEY to your .env or environment.")
        return False
    return True


def _build_session(retries: int = 3, backoff: float = 1.0) -> requests.Session:
    """Create a requests Session with retry/backoff for transient errors."""
    session = requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET", "POST"),
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def get_place_reviews(place_id: str) -> List[Dict[str, Any]]:
    """Fetch reviews for a specific Google Maps place via SerpApi."""
    if not _check_api_key():
        return []

    params = {
        "engine": "google_maps_reviews",
        "place_id": place_id,
        "api_key": SERPAPI_KEY,
    }

    session = _build_session()
    try:
        resp = session.get("https://serpapi.com/search", params=params, timeout=10)
        print(f"[SerpAPI] get_place_reviews status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"[SerpAPI] get_place_reviews response: {resp.text}")
            return []
        data = resp.json()
        if isinstance(data, dict):
            return data.get("reviews", [])
        return []
    except Exception as e:
        print(f"[Error] get_place_reviews: {e}")
        return []


def get_reviews_google_maps(query: str, location: str, num: int ) -> List[Dict[str, Any]]:
    """Return list of reviews from local results via SerpApi.

    Note: SerpApi does not allow using both `location` and `ll` together. We use `ll` (center lat/lon)
    and include the textual `location` in the query string to bias results.
    """
    if not _check_api_key():
        return []

    # Build a query string that includes the location to bias results
    q = f"{query} {location or 'CABA'}"

    params = {
        "engine": "google_maps",
        "q": q,
        "type": "search",
        "ll": "@-34.6037,-58.3816,13z",
        "google_domain": "google.com.ar",
        "gl": "ar",
        "hl": "en",
        "api_key": SERPAPI_KEY,
    }

    session = _build_session()
    try:
        resp = session.get("https://serpapi.com/search", params=params, timeout=10)
        print(f"[Debug] Status Code: {resp.status_code}")
        if resp.status_code != 200:
            print(f"[SerpAPI] Response: {resp.text}")
            return []
        data = resp.json()
        local_results = data.get("local_results", []) if isinstance(data, dict) else []
        print(f"[Debug] Resultados encontrados: {len(local_results)}")
    except Exception as e:
        print(f"[Error] Error en la búsqueda: {e}")
        return []

    if not local_results:
        print("[Error] No se encontraron resultados locales")
        return []

    reviews_list: List[Dict[str, Any]] = []

    for place in local_results[:num]:
        place_id = place.get("place_id")
        name = place.get("title")
        gps = place.get("gps_coordinates") or {}
        lat = gps.get("latitude")
        lon = gps.get("longitude")

        # Filter by approximate Buenos Aires bounding box
        if lat is not None and lon is not None:
            try:
                lat = float(lat)
                lon = float(lon)
            except Exception:
                lat = None
                lon = None

        if lat is not None and lon is not None:
            lat_min, lat_max = -34.7, -34.5
            lon_min, lon_max = -58.5, -58.3
            if not (lat_min <= lat <= lat_max and lon_min <= lon <= lon_max):
                print(f"[Debug] Descartando {name} - fuera de Buenos Aires")
                continue

        # Fetch place reviews
        try:
            place_reviews = get_place_reviews(place_id)
            print(f"[Debug] Reseñas encontradas para {name}: {len(place_reviews)}")
            for r in place_reviews:
                snippet = r.get("snippet") or r.get("excerpt") or r.get("text")
                reviews_list.append({
                    "place_id": place_id,
                    "name": name,
                    "lat": lat,
                    "lon": lon,
                    "text": snippet,
                    "rating": r.get("rating"),
                    "created_at": r.get("time"),
                    "source": "Google Maps",
                })
        except Exception as e:
            print(f"[Error] Error obteniendo reseñas para {name}: {e}")
            continue

    print(f"[Info] Se encontraron {len(reviews_list)} reseñas en total")
    return reviews_list
