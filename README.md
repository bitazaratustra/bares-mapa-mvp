# MVP: Mapa de Bares y Restaurantes en Buenos Aires

Este proyecto es un **MVP de minería de textos y visualización geoespacial** desarrollado en Python con FastAPI y PostgreSQL. Permite:

- Scrappear reseñas de Google Maps usando SerpApi.
- Guardarlas en PostgreSQL.
- Aplicar **topic modeling** con BERTopic y embeddings multilingües.
- Asignar cada reseña a una **celda geoespacial H3**.
- Visualizar un mapa interactivo con capas filtrables por topic.

---

## ⚙️ Requisitos

- Python 3.10+
- PostgreSQL
- SerpApi API key

Instalación de dependencias:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

🛠️ Flujo de trabajo
1️⃣ Inicializar la base de datos

Ejecutar SQL:
psql -U postgres -f init_db.sql

Luego inicializar tablas:

make init_db

2️⃣ Scrappear reseñas
make scrape


Scrapea bares y restaurantes de Buenos Aires y guarda las reseñas en la base de datos. Si no hay datos reales, se usan ejemplos.

3️⃣ Generar topics y H3
make topic


Limpia y preprocesa los textos.

Aplica BERTopic para generar topics automáticos.

Calcula el índice geoespacial H3 para cada reseña.

4️⃣ Ejecutar servidor FastAPI
make run


Endpoints:

GET /reviews/scrape → Ejecuta scraping.

GET /maps?topic_filter=0 → Devuelve reseñas agrupadas por H3, filtradas por topic (opcional).

5️⃣ Visualizar el mapa

Abrir en navegador:

http://127.0.0.1:8000/static/reviews_map.html


Cada celda H3 se dibuja como polígono azul.

Al hacer click, se muestran las reseñas de esa celda.

El dropdown permite filtrar por topic.
