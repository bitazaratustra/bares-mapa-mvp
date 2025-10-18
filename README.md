# MVP: Mapa de Bares y Restaurantes con Recomendaciones por Similitud

Este proyecto es un MVP desarrollado con FastAPI, PostgreSQL y técnicas de NLP que permite explorar y encontrar bares/restaurantes similares basados en sus reseñas y características.

## 🌟 Funcionalidades

- 🗺️ **Visualización geográfica**: Mapa interactivo con bares y restaurantes
- 🤖 **Procesamiento de texto**: Análisis de reseñas usando embeddings de lenguaje
- 🔍 **Búsqueda semántica**: Encuentra lugares similares usando similitud coseno
- 📊 **Agrupación por tópicos**: Agrupa lugares por temáticas comunes
- 🏙️ **Filtrado por barrios**: Explora lugares por zonas de Buenos Aires

## 🛠️ Requisitos Técnicos

- Python 3.10+
- PostgreSQL 12+
- 2GB RAM mínimo

## 📦 Instalación

1. **Clonar el repositorio**:
```bash
git clone https://github.com/username/bares-mapa-mvp
cd bares-mapa-mvp
```

2. **Crear y activar entorno virtual**:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. **Instalar dependencias**:
```bash
pip install -r requirements.txt
```

4. **Configurar PostgreSQL**:
```sql
CREATE DATABASE bares_db;
CREATE USER esteban WITH PASSWORD '1234';
GRANT ALL PRIVILEGES ON DATABASE bares_db TO esteban;
```

## 🚀 Ejecución

1. **Inicializar la base de datos**:
```bash
make init_db
```

2. **Crear datos de ejemplo** (requerido para el primer uso):
```bash
make samples
```

3. **Generar embeddings y tópicos**:
```bash
make topic
make embeddings
```

4. **Ejecutar la aplicación**:
```bash
make run
```

La aplicación estará disponible en: http://localhost:8000

## 🗺️ Uso del Mapa

1. Abre http://localhost:8000 en tu navegador
2. Usa los filtros en la parte superior para:
   - Seleccionar un barrio específico
   - Filtrar por tipo de tópico (ej: bares, restaurantes, etc.)
3. Haz clic en los marcadores para ver detalles
4. Usa el botón "Ver lugares similares" para encontrar recomendaciones

## 🤖 Sistema de Recomendación

El sistema utiliza:
- Embeddings de [paraphrase-MiniLM-L3-v2](https://huggingface.co/sentence-transformers/paraphrase-MiniLM-L3-v2)
- Clustering con KMeans para identificar tópicos
- Similitud coseno para encontrar lugares similares

## 📂 Estructura del Proyecto

```
app/
├── db/             # Configuración de base de datos
├── models/         # Modelos SQLAlchemy
├── routes/         # Endpoints FastAPI
├── services/       # Lógica de negocio
└── static/         # Frontend y assets

```

## 🔄 Makefile Commands

- `make init_db`: Inicializa la base de datos
- `make samples`: Crea datos de ejemplo
- `make topic`: Ejecuta modelado de tópicos
- `make embeddings`: Precalcula embeddings
- `make run`: Inicia el servidor FastAPI
- `make full_setup`: Ejecuta todo el proceso de setup

## 🤝 Contribuciones

Este es un MVP para fines académicos. Siéntete libre de:
1. Fork el repositorio
2. Crear una rama (`git checkout -b feature/mejora`)
3. Commit tus cambios (`git commit -m 'Agrega mejora'`)
4. Push a la rama (`git push origin feature/mejora`)
5. Crear un Pull Request

## 📝 Notas

- Los datos de ejemplo son generados artificialmente para demostración
- El sistema está optimizado para recursos limitados (usa un modelo liviano)
- Recomendado usar Chrome o Firefox para mejor experiencia en el mapa
