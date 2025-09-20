import psycopg2
import random
from datetime import datetime
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import re
import nltk
from nltk.corpus import stopwords

# Datos de conexión a la base de datos
DB_CONFIG = {
    "dbname": "bares_db",
    "user": "esteban",
    "password": "1234",
    "host": "localhost",
    "port": "5432"
}

# Barrios de Buenos Aires
NEIGHBORHOODS = ["Palermo", "Recoleta", "San Telmo", "Belgrano", "Caballito", 
                "Villa Crespo", "Almagro", "Puerto Madero", "Colegiales", "Chacarita"]

# Nombres de bares y restaurantes con sus coordenadas exactas
PLACES_WITH_COORDINATES = {
    "La Birra Bar": {"lat": -34.6037, "lon": -58.3816},
    "El Primo": {"lat": -34.5885, "lon": -58.4304},
    "Don Julio": {"lat": -34.5897, "lon": -58.4312},
    "La Cabrera": {"lat": -34.5882, "lon": -58.4301},
    "Cabaña Las Lilas": {"lat": -34.6086, "lon": -58.3783},
    "Tegui": {"lat": -34.5889, "lon": -58.4305},
    "Osaka": {"lat": -34.5893, "lon": -58.4310},
    "Siamo Nel Forno": {"lat": -34.5888, "lon": -58.4308},
    "La Carnicería": {"lat": -34.5884, "lon": -58.4303},
    "El Preferido de Palermo": {"lat": -34.5886, "lon": -58.4306},
    "La Mar": {"lat": -34.5890, "lon": -58.4309},
    "Parrilla Peña": {"lat": -34.5891, "lon": -58.4311},
    "El Sanjuanino": {"lat": -34.5892, "lon": -58.4313},
    "Café Tortoni": {"lat": -34.6087, "lon": -58.3783},
    "El Obrero": {"lat": -34.6350, "lon": -58.3810},
    "La Brigada": {"lat": -34.6200, "lon": -58.3710},
    "El Cuartito": {"lat": -34.6035, "lon": -58.3815},
    "Las Cuartetas": {"lat": -34.6036, "lon": -58.3814},
    "El Ateneo": {"lat": -34.6038, "lon": -58.3817},
    "El Gato Negro": {"lat": -34.6039, "lon": -58.3818}
}

# Textos de reseñas de ejemplo
REVIEW_TEXTS = [
    "Excelente ambiente y buena música. La comida es deliciosa, especialmente las empanadas.",
    "Muy buen servicio y precios accesibles. Ideal para ir con amigos.",
    "La carne estaba en su punto perfecto. El lugar tiene una terraza increíble.",
    "Buena selección de cervezas artesanales. El personal es muy amable.",
    "Ambiente cálido y acogedor. Perfecto para una cena romántica.",
    "La pizza es espectacular, masa crocante y ingredientes frescos.",
    "Tienen live music los fines de semana. Muy divertido y buena energía.",
    "Cocktails creativos y deliciosos. Precios un poco elevados pero vale la pena.",
    "El mejor lugar para probar vinos argentinos. Sommelier muy conocedor.",
    "Terraza con vista privilegiada. Ideal para atardeceres.",
    "Comida italiana auténtica. La pasta es casera y exquisita.",
    "Hamburguesas jugosas y papas crocantes. Rápido servicio.",
    "Postres caseros increíbles. El flan con dulce de leche es imperdible.",
    "Desayunos abundantes y deliciosos. Buen café.",
    "Ambiente moderno y decoración interesante. Buena para fotos.",
    "Platos vegetarianos sabrosos y creativos. Opciones veganas también.",
    "Servicio rápido y eficiente. Perfecto para almuerzos de trabajo.",
    "Tienen juegos de mesa para divertirse mientras se come.",
    "Carta de vinos extensa y bien seleccionada.",
    "Ubicación céntrica y fácil acceso. Buena conexión de transporte."
]

# Palabras clave para generar tópicos
TOPIC_KEYWORDS = [
    "carne asado parrilla",
    "cerveza artesanal",
    "pizza italiana",
    "cocktails tragos",
    "música en vivo",
    "terraza vista",
    "postres dulces",
    "desayuno café",
    "vegetariano vegano",
    "vino malbec"
]

# Variable global para stopwords
STOPWORDS = set()

def preprocess(text):
    """Función de preprocesamiento de texto"""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"[^a-záéíóúüñ ]", "", text)
    tokens = text.split()
    tokens = [t for t in tokens if t not in STOPWORDS and len(t) > 2]
    return " ".join(tokens)

def assign_topic_numbers(review_texts):
    """Asigna números de tópico basados en similitud de embeddings"""
    # Generar embeddings para las palabras clave de tópicos
    model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    topic_embeddings = model.encode(TOPIC_KEYWORDS)
    
    # Asignar tópicos a las reseñas
    topic_numbers = []
    for text in review_texts:
        text_embedding = model.encode([text])
        similarities = cosine_similarity(text_embedding, topic_embeddings)[0]
        topic_idx = np.argmax(similarities)
        topic_numbers.append(topic_idx)
    
    return topic_numbers

def create_sample_data():
    try:
        # Conectar a la base de datos
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # TRUNCATE la tabla existente (más eficiente que DELETE) :cite[1]:cite[4]
        cur.execute("TRUNCATE TABLE reviews RESTART IDENTITY CASCADE;")
        
        # Preparar datos
        all_review_texts = []
        sample_data = []
        place_id_counter = 1
        
        for neighborhood in NEIGHBORHOODS:
            for i in range(5):  # 5 lugares por barrio
                place_name = random.choice(list(PLACES_WITH_COORDINATES.keys()))
                
                # Obtener coordenadas exactas para este lugar
                coords = PLACES_WITH_COORDINATES[place_name]
                lat = coords["lat"]
                lon = coords["lon"]
                
                rating = round(random.uniform(3.5, 5.0), 1)
                review_text = random.choice(REVIEW_TEXTS)
                
                # Crear un place_id único
                place_id = f"place_{place_id_counter}_{neighborhood.lower()}"
                place_id_counter += 1
                
                sample_data.append({
                    "place_id": place_id,
                    "name": f"{place_name} - {neighborhood}",
                    "lat": lat,
                    "lon": lon,
                    "rating": rating,
                    "text": review_text
                })
                
                all_review_texts.append(review_text)
        
        # Asignar números de tópico basados en similitud semántica
        topic_numbers = assign_topic_numbers(all_review_texts)
        
        # Insertar en la base de datos
        for i, data in enumerate(sample_data):
            cur.execute(
                "INSERT INTO reviews (place_id, name, lat, lon, rating, text, topic, source, created_at, embedding) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (data["place_id"], data["name"], data["lat"], data["lon"], data["rating"], 
                data["text"], int(topic_numbers[i]), "sample_data", datetime.now(), None)
            )
                    
        # Confirmar cambios
        conn.commit()
        print("Datos de ejemplo insertados correctamente.")
        print(f"Se insertaron {len(sample_data)} reseñas con números de tópico asignados.")
        
        # Cerrar conexión
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Error al insertar datos de ejemplo: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Descargar stopwords si no están disponibles
    try:
        nltk.data.find('corpora/stopwords')
        STOPWORDS = set(stopwords.words("spanish"))
    except LookupError:
        nltk.download('stopwords')
        STOPWORDS = set(stopwords.words("spanish"))
    
    create_sample_data()