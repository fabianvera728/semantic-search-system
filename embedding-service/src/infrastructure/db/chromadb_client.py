import os
import logging
import chromadb
from chromadb.config import Settings
from typing import Optional

logger = logging.getLogger(__name__)

_client = None


async def get_chromadb_client() -> chromadb.Client:
    global _client
    
    if _client is not None:
        return _client
    
    # Get configuration from environment variables
    host = os.getenv("CHROMADB_HOST", "chromadb")
    port = int(os.getenv("CHROMADB_PORT", "8000"))
    persistence_path = os.getenv("CHROMADB_PERSISTENCE_PATH", "/app/storage/chroma")
    
    # Create the persistence directory if it doesn't exist
    os.makedirs(persistence_path, exist_ok=True)
    
    try:
        # Try to connect to ChromaDB as a service first
        _client = chromadb.HttpClient(
            host=host,
            port=port,
            settings=Settings(
                allow_reset=True,
                anonymized_telemetry=False
            )
        )
        logger.info(f"Connected to ChromaDB service at {host}:{port}")
        
        # Test the connection
        _client.heartbeat()
        return _client
    except Exception as e:
        logger.warning(f"Could not connect to ChromaDB service: {str(e)}")
        logger.info(f"Falling back to persistent ChromaDB with path: {persistence_path}")
        
        # Fallback to persistent mode
        _client = chromadb.PersistentClient(
            path=persistence_path,
            settings=Settings(
                allow_reset=True,
                anonymized_telemetry=False
            )
        )
        
        return _client


def get_or_create_collection(client: chromadb.Client, name: str, metadata=None):
    try:
        collection = client.get_collection(name=name)
        logger.info(f"Retrieved existing collection: {name}")
        return collection
    except ValueError:
        logger.info(f"Creating new collection: {name}")
        return client.create_collection(
            name=name,
            metadata=metadata or {}
        ) 