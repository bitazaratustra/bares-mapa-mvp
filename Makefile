# Makefile para MVP Bares BA

.PHONY: init_db run scrape topic clean embeddings full_setup samples

# Inicializar base de datos (crear tablas)
init_db:
	python -c "from app.db.database import engine; from app.db.init_db import Base; Base.metadata.create_all(bind=engine)"
	@echo "Base de datos inicializada"

# Crear datos de ejemplo con coordenadas corregidas
samples:
	python -m app.services.create_samples
	@echo "Datos de ejemplo creados"

# Ejecutar FastAPI
run:
	uvicorn app.main:app --workers 1 --timeout-keep-alive 30 --reload

# Scrapear reseñas (no disponible hasta renovar licencia)
scrape:
	python -m app.services.scrape_utils
	@echo "Scraping completado y reseñas guardadas en la base de datos"

# Generar topics + H3
topic:
	python -c "from app.db.database import get_db; from app.services.topic_model_utils import run_topic_modeling; db = next(get_db()); run_topic_modeling(db); print('Topic modeling completado')"

# Precalcular embeddings
embeddings:
	python -c "from app.db.database import get_db; from app.services.topic_model_utils import precompute_embeddings; db = next(get_db()); precompute_embeddings(db); print('Embeddings precomputados')"

# Proceso completo de setup
full_setup: init_db samples topic embeddings
	@echo "Setup completo realizado"

# Limpiar archivos generados
clean:
	rm -f app/static/reviews.json
	@echo "Archivos limpiados"




# Para realizar prueba con datos sinteticos:

# make init_db # 1. Inicializar la base de datos (crear tablas)
# make samples # 2. Crear datos de ejemplo con coordenadas corregidas
# make topic # 3. Ejecutar el modelado de tópicos
# make embeddings # 4. Precalcular embeddings
# make run # 5. Ejecutar la aplicación




# Para scraping real :

# make init_db # Inicializar la base de datos (crear tablas)
# make scrape  # Reemplazará los datos de ejemplo con datos reales
# make topic   # Re-ejecutar el modelado de tópicos con datos reales
# make embeddings  # Re-calcular embeddings con datos reales
# make run     # Reiniciar la aplicación