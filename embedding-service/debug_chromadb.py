#!/usr/bin/env python3
"""
Script de diagnóstico para ChromaDB
Verifica el estado de las colecciones y ayuda a diagnosticar problemas
"""

import asyncio
import logging
import os
import sys
from datetime import datetime

# Agregar el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.infrastructure.db import get_chromadb_client

# Configurar logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def diagnose_chromadb():
    """Función principal de diagnóstico"""
    try:
        logger.info("🔍 Iniciando diagnóstico de ChromaDB...")
        
        # Obtener cliente
        client = await get_chromadb_client()
        logger.info("✅ Conexión a ChromaDB establecida")
        
        # Verificar heartbeat
        try:
            heartbeat = client.heartbeat()
            logger.info(f"💓 Heartbeat: {heartbeat}")
        except Exception as e:
            logger.error(f"❌ Error en heartbeat: {e}")
            return
        
        # Listar todas las colecciones
        try:
            collections = client.list_collections()
            logger.info(f"📊 Total de colecciones encontradas: {len(collections)}")
            
            for i, collection in enumerate(collections):
                logger.info(f"  {i+1}. {collection.name}")
                
                # Obtener información detallada de cada colección
                try:
                    col_obj = client.get_collection(collection.name)
                    count = col_obj.count()
                    metadata = getattr(col_obj, 'metadata', {})
                    logger.info(f"     📈 Elementos: {count}")
                    logger.info(f"     📋 Metadata: {metadata}")
                    
                    # Verificar si es una colección de dataset
                    if collection.name.startswith('dataset_'):
                        dataset_id = collection.name.replace('dataset_', '')
                        logger.info(f"     🗂️  Dataset ID: {dataset_id}")
                        
                        # Intentar obtener algunos elementos
                        try:
                            result = col_obj.get(limit=3, include=["metadatas", "documents"])
                            if result["ids"]:
                                logger.info(f"     📄 Primeros elementos: {result['ids'][:3]}")
                            else:
                                logger.info(f"     📄 Colección vacía")
                        except Exception as get_err:
                            logger.warning(f"     ⚠️  Error obteniendo elementos: {get_err}")
                            
                except Exception as col_err:
                    logger.error(f"     ❌ Error accediendo a colección {collection.name}: {col_err}")
                    
        except Exception as e:
            logger.error(f"❌ Error listando colecciones: {e}")
            return
        
        # Verificar colección específica si se proporciona dataset_id
        dataset_id = os.getenv('DATASET_ID')
        if dataset_id:
            logger.info(f"\n🔍 Verificando dataset específico: {dataset_id}")
            collection_name = f"dataset_{dataset_id}"
            
            try:
                collection = client.get_collection(collection_name)
                count = collection.count()
                logger.info(f"✅ Colección {collection_name} encontrada con {count} elementos")
                
                # Obtener algunos elementos
                result = collection.get(limit=5, include=["metadatas", "documents"])
                logger.info(f"📄 IDs de elementos: {result['ids']}")
                
            except ValueError as ve:
                logger.error(f"❌ Colección {collection_name} no encontrada: {ve}")
            except Exception as e:
                logger.error(f"❌ Error accediendo a colección {collection_name}: {e}")
        
        # Verificar colección de metadatos
        logger.info(f"\n🔍 Verificando colección de metadatos...")
        try:
            metadata_collection = client.get_collection("datasets_metadata")
            count = metadata_collection.count()
            logger.info(f"✅ Colección datasets_metadata encontrada con {count} elementos")
            
            result = metadata_collection.get(include=["metadatas"])
            if result["ids"]:
                logger.info(f"📄 Datasets registrados: {result['ids']}")
            else:
                logger.info(f"📄 No hay datasets registrados en metadatos")
                
        except ValueError:
            logger.warning(f"⚠️  Colección datasets_metadata no encontrada")
        except Exception as e:
            logger.error(f"❌ Error accediendo a colección datasets_metadata: {e}")
        
        logger.info("\n✅ Diagnóstico completado")
        
    except Exception as e:
        logger.error(f"❌ Error general en diagnóstico: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🩺 ChromaDB Diagnostic Tool")
    print("=" * 50)
    print("Variables de entorno útiles:")
    print(f"CHROMADB_HOST: {os.getenv('CHROMADB_HOST', 'chromadb')}")
    print(f"CHROMADB_PORT: {os.getenv('CHROMADB_PORT', '8000')}")
    print(f"DATASET_ID: {os.getenv('DATASET_ID', 'No especificado')}")
    print("=" * 50)
    
    asyncio.run(diagnose_chromadb()) 