from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.routes.reviews import router as reviews_router
from app.routes.maps import router as maps_router
from app.routes.topic_model import router as topic_model_router

app = FastAPI(title="Bares BA MVP")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(reviews_router, prefix="/reviews")
app.include_router(maps_router, prefix="/maps")
app.include_router(topic_model_router, prefix="/topic_model")

# Servir archivos estáticos
app.mount("/", StaticFiles(directory="app/static", html=True), name="static")
