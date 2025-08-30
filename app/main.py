from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routes.reviews import router as reviews_router
from app.routes.maps import router as maps_router

app = FastAPI(title="Bares BA MVP")

app.include_router(reviews_router, prefix="/reviews")
app.include_router(maps_router, prefix="/maps")

# Servir archivos estáticos (mapa)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
