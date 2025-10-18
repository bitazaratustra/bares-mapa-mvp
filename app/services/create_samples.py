import psycopg2
import random
from datetime import datetime, timedelta
from sentence_transformers import SentenceTransformer
import numpy as np

# Configuración
DB_CONFIG = {
    "dbname": "bares_db",
    "user": "esteban",
    "password": "1234",
    "host": "localhost",
    "port": "5432"
}

# Datos de ejemplo realistas
NEIGHBORHOODS = {
    "Palermo": {"lat_base": -34.5885, "lon_base": -58.4304, "radius": 0.01},
    "Recoleta": {"lat_base": -34.5873, "lon_base": -58.3920, "radius": 0.008},
    "San Telmo": {"lat_base": -34.6200, "lon_base": -58.3720, "radius": 0.007},
    "Belgrano": {"lat_base": -34.5580, "lon_base": -58.4590, "radius": 0.009},
    "Villa Crespo": {"lat_base": -34.5980, "lon_base": -58.4420, "radius": 0.008},
}

# Tipos de lugares con nombres realistas
PLACE_TYPES = {
    "bar": [
        "Bar Los Amigos", "La Birra Bar", "El Taller", "Bar El Progreso", 
        "La Popular", "Bar La Paz", "Santos Bar", "El Preferido", 
        "La Catalana", "Café Bar El Federal", "Bar El Británico",
        "La Poesía", "Bar Notable", "La Academia"
    ],
    "restaurante": [
        "Don Julio", "La Cabrera", "Proper", "Gran Dabbang", "Tegui",
        "El Preferido de Palermo", "Las Pizarras", "La Carnicería",
        "Mishiguene", "Oporto Almacén", "El Obrero", "La Brigada",
        "Café San Juan", "Aramburu", "El Mercado"
    ],
    "cafeteria": [
        "Café Tortoni", "Las Violetas", "La Biela", "El Gato Negro",
        "Café de los Angelitos", "Café Margot", "Le Pain Quotidien",
        "Café Martinez", "Havanna Café", "La Esperanza", "Café Paulin",
        "Lab Café", "Coffee Town", "Full City Coffee House"
    ]
}

# Reviews realistas por tipo de lugar
REVIEW_TEMPLATES = {
    "bar": [
        "La cerveza artesanal es excelente, {ambiente}. {servicio}. {precio}",
        "Gran selección de tragos, {ambiente}. {música}. {precio}",
        "El lugar ideal para after office, {ambiente}. {servicio}. {comida}",
        "Muy buena música en vivo, {ambiente}. {servicio}. {precio}",
        "{ambiente} y {música}. Los cocktails son creativos. {precio}"
    ],
    "restaurante": [
        "La comida es espectacular, {servicio}. {ambiente}. {precio}",
        "Excelente {comida}. {servicio}. {ambiente}",
        "Vale la pena la espera, {comida}. {ambiente}. {precio}",
        "Un clásico que nunca falla. {comida}. {servicio}",
        "La mejor relación precio-calidad. {comida}. {ambiente}"
    ],
    "cafeteria": [
        "El café es de primera, {ambiente}. {servicio}. {precio}",
        "Excelentes medialunas, {ambiente}. {servicio}. {comida}",
        "Ideal para trabajar, {ambiente}. {servicio}. {wifi}",
        "Gran lugar para desayunar, {comida}. {servicio}",
        "El brunch es imperdible, {comida}. {ambiente}. {precio}"
    ]
}

# Componentes para generar reviews
AMBIENTE = [
    "ambiente muy acogedor", "decoración moderna", "lugar histórico",
    "espacio amplio y cómodo", "ambiente relajado", "local con onda",
    "decoración vintage", "lugar muy pintoresco", "ambiente íntimo"
]

SERVICIO = [
    "servicio atento y profesional", "personal muy amable",
    "excelente atención", "servicio rápido y eficiente",
    "los mozos son muy atentos", "gran profesionalismo",
    "atención personalizada", "staff muy cordial"
]

COMIDA = [
    "platos muy bien servidos", "porciones generosas",
    "sabores auténticos", "comida casera de calidad",
    "ingredientes frescos", "presentación impecable",
    "carta variada", "opciones vegetarianas disponibles"
]

MUSICA = [
    "buena selección musical", "música en vivo los fines de semana",
    "volumen adecuado para conversar", "playlist muy bien curada",
    "shows de jazz en vivo", "música ambiente agradable"
]

PRECIO = [
    "precios razonables", "buena relación precio-calidad",
    "un poco caro pero vale la pena", "precios acordes a la calidad",
    "bastante económico para la zona", "precios de mercado"
]

WIFI = [
    "buen wifi", "wifi rápido y estable",
    "conexión gratuita", "señal excelente de wifi"
]

def generate_review(place_type):
    """Genera una review realista basada en el tipo de lugar"""
    template = random.choice(REVIEW_TEMPLATES[place_type])
    return template.format(
        ambiente=random.choice(AMBIENTE),
        servicio=random.choice(SERVICIO),
        comida=random.choice(COMIDA),
        música=random.choice(MUSICA),
        precio=random.choice(PRECIO),
        wifi=random.choice(WIFI)
    )

def generate_random_coordinates(base_lat, base_lon, radius):
    """Genera coordenadas aleatorias dentro de un radio"""
    r = radius * np.sqrt(random.random())
    theta = random.random() * 2 * np.pi
    return {
        "lat": base_lat + r * np.cos(theta),
        "lon": base_lon + r * np.sin(theta)
    }

def create_sample_data(num_places_per_neighborhood=5):
    """Crea datos de ejemplo realistas para la base de datos"""
    try:
        # Conectar a la base de datos
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Limpiar tabla
        cur.execute("TRUNCATE TABLE reviews RESTART IDENTITY CASCADE;")
        
        # Modelo para embeddings
        model = SentenceTransformer("paraphrase-MiniLM-L3-v2")
        print("[Setup] Modelo de embeddings cargado")
        
        # Contador de registros
        total_reviews = 0
        
        # Para cada barrio
        for neighborhood, coords in NEIGHBORHOODS.items():
            print(f"\n[Generando] Datos para {neighborhood}")
            
            # Para cada tipo de lugar
            for place_type, places in PLACE_TYPES.items():
                # Seleccionar lugares aleatorios para este barrio
                selected_places = random.sample(places, min(num_places_per_neighborhood, len(places)))
                
                for place_name in selected_places:
                    # Generar ubicación realista
                    location = generate_random_coordinates(
                        coords["lat_base"], 
                        coords["lon_base"], 
                        coords["radius"]
                    )
                    
                    # Generar entre 3 y 5 reviews por lugar
                    num_reviews = random.randint(3, 5)
                    for _ in range(num_reviews):
                        # Generar review
                        review_text = generate_review(place_type)
                        rating = round(random.uniform(3.5, 5.0), 1)
                        
                        # Generar fecha en los últimos 6 meses
                        days_ago = random.randint(0, 180)
                        created_at = datetime.now() - timedelta(days=days_ago)
                        
                        # Generar place_id único
                        place_id = f"place_{neighborhood.lower()}_{total_reviews}"
                        
                        # Generar embedding
                        text_for_embedding = f"{place_name} {review_text}"
                        embedding = model.encode(text_for_embedding).tolist()
                        
                        # Insertar en la base de datos
                        cur.execute("""
                            INSERT INTO reviews (
                                place_id, name, lat, lon, rating, text, 
                                created_at, source, embedding
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            place_id,
                            f"{place_name} - {neighborhood}",
                            location["lat"],
                            location["lon"],
                            rating,
                            review_text,
                            created_at,
                            "sample_data",
                            embedding
                        ))
                        
                        total_reviews += 1
                        
                        # Commit cada 10 registros
                        if total_reviews % 10 == 0:
                            conn.commit()
                            print(f"[Progreso] {total_reviews} reseñas creadas")
        
        # Commit final
        conn.commit()
        print(f"\n[Completado] {total_reviews} reseñas creadas exitosamente")
        
    except Exception as e:
        print(f"Error creando datos de ejemplo: {str(e)}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    create_sample_data()