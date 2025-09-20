from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.routes import reviews, maps, topic_model

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
app.include_router(reviews.router, prefix="/reviews")
app.include_router(maps.router, prefix="/maps")
app.include_router(topic_model.router, prefix="/topic_model")

# Servir archivos estáticos
app.mount("/", StaticFiles(directory="app/static", html=True), name="static")