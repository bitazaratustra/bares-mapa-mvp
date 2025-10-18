# Restauración del Sistema MVP

## 1. Configuración Inicial

### 1.1 Base de datos
```bash
# Como usuario postgres
sudo -u postgres psql

# En psql:
CREATE DATABASE bares_db;
CREATE USER esteban WITH PASSWORD '1234';
GRANT ALL PRIVILEGES ON DATABASE bares_db TO esteban;
\c bares_db
GRANT ALL ON ALL TABLES IN SCHEMA public TO esteban;
```

### 1.2 Entorno Python
```bash
# Crear y activar entorno virtual
python -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

## 2. Restaurar el Sistema

### 2.1 Probar el flujo completo
```bash
# Ejecutar script de prueba
python test_flow.py
```

### 2.2 Iniciar el servidor
```bash
# Usando make
make run

# O directamente
uvicorn app.main:app --reload
```

## 3. Estructura del Sistema

### 3.1 Componentes Principales
- `app/db/`: Configuración de base de datos y modelos
- `app/services/`: Lógica de negocio y procesamiento
- `app/routes/`: Endpoints de la API
- `app/static/`: Frontend y assets

### 3.2 Flujo de Datos
1. Los datos de ejemplo se generan con coordenadas realistas
2. Los embeddings se precomputan usando un modelo ligero
3. El clustering agrupa las reseñas en tópicos
4. La búsqueda utiliza similitud coseno para recomendaciones

## 4. Troubleshooting

### 4.1 Problemas Comunes
- Error de conexión a PostgreSQL: Verificar credenciales en DATABASE_URL
- Error de memoria: Reducir BATCH_SIZE en topic_model_utils.py
- Error de dependencias: Actualizar requirements.txt

### 4.2 Comandos Útiles
```bash
# Reiniciar la base de datos
make init_db

# Recrear datos de ejemplo
make samples

# Regenerar embeddings y tópicos
make topic
make embeddings
```

## 5. Endpoints API

### 5.1 Principales Endpoints
- GET /maps: Visualización de reseñas en mapa
- POST /topic_model/search: Búsqueda por similitud
- GET /reviews/neighborhoods: Lista de barrios disponibles
- GET /topic_model/topics: Lista de tópicos disponibles

### 5.2 Uso del Frontend
1. Acceder a http://localhost:8000
2. Seleccionar barrio y/o tópico
3. Explorar lugares en el mapa
4. Ver recomendaciones similares