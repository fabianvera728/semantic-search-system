from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from uuid import UUID
import numpy as np

from .entities import Embedding, EmbeddingBatch, Dataset, EmbeddingModel
from .value_objects import (
    GenerateEmbeddingRequest,
    BatchEmbeddingRequest,
    ListEmbeddingsRequest,
    GetEmbeddingRequest,
    DeleteEmbeddingRequest,
    CreateDatasetRequest,
    ProcessDatasetRowsRequest
)


class EmbeddingRepository(ABC):
    @abstractmethod
    async def generate_embedding(self, request: GenerateEmbeddingRequest) -> Embedding:
        """Generate a single embedding"""
        pass
    
    @abstractmethod
    async def generate_batch_embeddings(self, request: BatchEmbeddingRequest) -> EmbeddingBatch:
        """Generate embeddings for a batch of texts"""
        pass
    
    @abstractmethod
    async def save_embedding(self, embedding: Embedding) -> Embedding:
        """Save a single embedding to the database"""
        pass
    
    @abstractmethod
    async def save_batch_embeddings(self, batch: EmbeddingBatch) -> EmbeddingBatch:
        """Save a batch of embeddings to the database"""
        pass
    
    @abstractmethod
    async def get_embedding(self, request: GetEmbeddingRequest) -> Optional[Embedding]:
        """Get a single embedding from the database"""
        pass
    
    @abstractmethod
    async def list_embeddings(self, request: ListEmbeddingsRequest) -> List[Embedding]:
        """List embeddings from the database with pagination"""
        pass
    
    @abstractmethod
    async def delete_embedding(self, request: DeleteEmbeddingRequest) -> bool:
        """Delete a single embedding from the database"""
        pass
    
    @abstractmethod
    async def delete_dataset_embeddings(self, dataset_id: str) -> int:
        """Delete all embeddings for a dataset"""
        pass
    
    @abstractmethod
    async def get_models(self) -> List[EmbeddingModel]:
        """Get all available embedding models"""
        pass
    
    @abstractmethod
    async def get_model(self, model_name: str) -> Optional[EmbeddingModel]:
        """Get specific embedding model information"""
        pass


class DatasetRepository(ABC):
    @abstractmethod
    async def create_dataset(self, request: CreateDatasetRequest) -> Dataset:
        """Create a new dataset in the embedding store"""
        pass
    
    @abstractmethod
    async def get_dataset(self, dataset_id: str) -> Optional[Dataset]:
        """Get dataset information"""
        pass
    
    @abstractmethod
    async def delete_dataset(self, dataset_id: str) -> bool:
        """Delete a dataset from the embedding store"""
        pass
    
    @abstractmethod
    async def list_datasets(self, limit: int = 100, offset: int = 0) -> List[Dataset]:
        """List datasets with pagination"""
        pass
    
    @abstractmethod
    async def update_dataset(self, dataset: Dataset) -> Dataset:
        """Update dataset information"""
        pass


class DataStorageRepository(ABC):
    @abstractmethod
    async def get_dataset_rows(
        self, 
        dataset_id: str, 
        offset: int = 0, 
        limit: int = 100, 
        filter_criteria: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Get dataset rows from data storage service"""
        pass
    
    @abstractmethod
    async def get_dataset_row(
        self, 
        dataset_id: str, 
        row_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get specific dataset row from data storage service"""
        pass
    
    @abstractmethod
    async def get_dataset_info(self, dataset_id: str) -> Optional[Dict[str, Any]]:
        """Get dataset information from data storage service"""
        pass 