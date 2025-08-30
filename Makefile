# Makefile para MVP Bares BA

.PHONY: init_db run scrape topic clean

# Inicializar base de datos (solo si cambian modelos o es la primera vez)
init_db:
	python -c "from app.db.database import engine; from app.db.init_db import Base; Base.metadata.create_all(bind=engine)"

# Ejecutar FastAPI
run:
	uvicorn app.main:app --reload

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
