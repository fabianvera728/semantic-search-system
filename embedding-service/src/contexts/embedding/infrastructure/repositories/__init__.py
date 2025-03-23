import logging

from src.config import AppConfig
from src.contexts.embedding.infrastructure.repositories.chroma_embedding_repository import ChromaEmbeddingRepository
from src.contexts.embedding.infrastructure.repositories.chroma_dataset_repository import ChromaDatasetRepository
from src.contexts.embedding.domain import EmbeddingRepository, DatasetRepository

logger = logging.getLogger(__name__)


async def create_embedding_repository(config: AppConfig) -> EmbeddingRepository:
    """Create and return the appropriate embedding repository implementation."""
    if config.vector_db_type.lower() == "chromadb":
        logger.info("Using ChromaDB for embedding storage")
        return ChromaEmbeddingRepository(config)
    else:
        logger.info(f"Unknown vector DB type: {config.vector_db_type}, defaulting to ChromaDB")
        return ChromaEmbeddingRepository(config)


async def create_dataset_repository(config: AppConfig) -> DatasetRepository:
    """Create and return the appropriate dataset repository implementation."""
    if config.vector_db_type.lower() == "chromadb":
        logger.info("Using ChromaDB for dataset storage")
        return ChromaDatasetRepository(config)
    else:
        logger.info(f"Unknown vector DB type: {config.vector_db_type}, defaulting to ChromaDB")
        return ChromaDatasetRepository(config)


__all__ = [
    "create_embedding_repository",
    "create_dataset_repository",
] 