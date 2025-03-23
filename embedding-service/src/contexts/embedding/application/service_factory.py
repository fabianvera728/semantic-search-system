from typing import Dict, Any, Optional, Type

from .embedding_service import EmbeddingService
from ..domain import (
    EmbeddingRepository,
    DatasetRepository,
)


class ServiceFactory:
    """Factory to create application services with their dependencies."""
    
    def __init__(self):
        self._embedding_repository = None
        self._dataset_repository = None
    
    def register_embedding_repository(self, repository: EmbeddingRepository) -> None:
        """Register the embedding repository implementation."""
        self._embedding_repository = repository
    
    def register_dataset_repository(self, repository: DatasetRepository) -> None:
        """Register the dataset repository implementation."""
        self._dataset_repository = repository
    
    def create_embedding_service(self) -> EmbeddingService:
        """Create and return a new instance of the EmbeddingService."""
        if not self._embedding_repository:
            raise ValueError("EmbeddingRepository not registered")
        
        if not self._dataset_repository:
            raise ValueError("DatasetRepository not registered")
        
        return EmbeddingService(
            embedding_repository=self._embedding_repository,
            dataset_repository=self._dataset_repository
        )


_factory = ServiceFactory()


def get_service_factory() -> ServiceFactory:
    """Get the singleton service factory instance."""
    return _factory


def create_embedding_service() -> EmbeddingService:
    """Create and return a new instance of the EmbeddingService using the factory."""
    return get_service_factory().create_embedding_service() 