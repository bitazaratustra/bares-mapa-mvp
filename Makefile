# Makefile para MVP Bares BA

.PHONY: init_db run scrape topic clean

# Inicializar base de datos (solo si cambian modelos o es la primera vez)
init_db:
	python -c "from app.db.database import engine; from app.db.init_db import Base; Base.metadata.create_all(bind=engine)"

initialize:
	python -m app.db.create_init_data

samples:
	python -m app.services.create_samples

# Ejecutar FastAPI
run:
	@echo "Stopping any existing process on port 8000..."
	-@lsof -ti:8000 | xargs kill -9 2>/dev/null || true
	@sleep 2
	uvicorn app.main:app --workers 1 --timeout-keep-alive 30 --reload

# Scrappear reseñas
scrape:
	python -m app.services.scrape_utils

# Generar topics + H3
topic:
	python -m app.services.topic_model

# Limpiar archivos generados (opcional)
clean:
	rm -f app/static/reviews.json


# Para hacer funcionar la app se deben ejecutar los siguiente comandos en orden:
# make init_db
# make scrape
# make topic
# make run
