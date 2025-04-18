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
        collection = client.get_collection(name=name)
        return collection
    except Exception as e:
        raise e
    
    # Si llegamos aquí, necesitamos crear la colección
    try:
        logger.info(f"Creating new collection: {name}")
        return client.create_collection(
            name=name,
            metadata=metadata
        )
    except Exception as create_err:
        logger.error(f"Failed to create collection {name}: {str(create_err)}")
        raise create_err 