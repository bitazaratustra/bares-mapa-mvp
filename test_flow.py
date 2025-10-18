"""
Script para probar el flujo completo del MVP
"""
import os
import sys
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.init_db import init_db
from app.services.create_samples import create_sample_data
from app.services.topic_model_utils import precompute_embeddings, run_topic_modeling

def test_full_flow():
    """Prueba el flujo completo del MVP"""
    try:
        print("\n1. Inicializando base de datos...")
        init_db()
        
        print("\n2. Creando datos de ejemplo...")
        create_sample_data(num_places_per_neighborhood=5)
        
        print("\n3. Generando embeddings...")
        db = next(get_db())
        precompute_embeddings(db)
        
        print("\n4. Ejecutando modelado de tópicos...")
        run_topic_modeling(db)
        
        print("\n✅ Flujo completo ejecutado exitosamente!")
        print("\nPuedes iniciar la aplicación con:")
        print("make run")
        print("\nY acceder a ella en: http://localhost:8000")
        
    except Exception as e:
        print(f"\n❌ Error durante la ejecución: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    test_full_flow()