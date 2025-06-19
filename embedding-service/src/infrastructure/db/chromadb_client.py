import os
import logging
import chromadb
from chromadb.config import Settings
from datetime import datetime

logger = logging.getLogger(__name__)

_client = None


async def get_chromadb_client() -> chromadb.Client:
    global _client
    
    if _client is not None:
        return _client
    
    host = os.getenv("CHROMADB_HOST", "chromadb")
    port = int(os.getenv("CHROMADB_PORT", "8000"))
    persistence_path = os.getenv("CHROMADB_PERSISTENCE_PATH", "/app/storage/chroma")
    
    os.makedirs(persistence_path, exist_ok=True)
    
    try:
        _client = chromadb.HttpClient(
            host=host,
            port=port,
            settings=Settings(
                allow_reset=True,
                anonymized_telemetry=False
            )
        )
        
        _client.heartbeat()
        return _client
    except Exception as e:
        raise e


def get_or_create_collection(client: chromadb.Client, name: str, metadata=None):
    if metadata is None or (isinstance(metadata, dict) and len(metadata) == 0):
        metadata = {"created_by": "embedding_service", "created_at": datetime.now().isoformat()}

    try:
        logger.debug(f"Attempting to get collection: {name}")
        collection = client.get_collection(name=name)
        logger.debug(f"Successfully retrieved existing collection: {name}")
        return collection
    except ValueError as ve:
        # ChromaDB lanza ValueError cuando la colección no existe
        logger.debug(f"Collection {name} not found (ValueError), creating new one: {str(ve)}")
    except Exception as e:
        # Para otros errores, logear más información
        logger.warning(f"Error getting collection {name}: {type(e).__name__}: {str(e)}")
        logger.debug(f"Attempting to create collection: {name}")
    
    # Si llegamos aquí, necesitamos crear la colección
    try:
        logger.info(f"Creating new collection: {name}")
        collection = client.create_collection(
            name=name,
            metadata=metadata
        )
        logger.info(f"Successfully created collection: {name}")
        return collection
    except Exception as create_err:
        logger.error(f"Failed to create collection {name}: {type(create_err).__name__}: {str(create_err)}")
        raise create_err 