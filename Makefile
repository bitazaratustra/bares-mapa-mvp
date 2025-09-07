# Makefile para MVP Bares BA

.PHONY: init_db run scrape topic clean

# Inicializar base de datos (solo si cambian modelos o es la primera vez)
init_db:
	python -c "from app.db.init_db import init_db; init_db()"

# Ejecutar FastAPI
run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Scrappear reseñas
scrape:
	python -m app.services.scrape_utils

# Generar topics + H3
topic:
	curl -X POST "http://localhost:8000/topic_model/run_topic_modeling"

# Limpiar archivos generados (opcional)
clean:
	rm -f app/static/reviews.json

# Para hacer funcionar la app se deben ejecutar los siguiente comandos en orden:
# make init_db
# make scrape
# make topic
# make run
# Open http://localhost:8000/static/reviews_map.html in your browser