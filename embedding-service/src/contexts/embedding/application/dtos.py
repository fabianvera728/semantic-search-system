from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class EmbeddingDTO(BaseModel):
    """DTO for embedding data"""
    embedding_id: UUID
    dataset_id: str
    row_id: str
    model_name: str
    dimension: int
    created_at: datetime
    vector: Optional[List[float]] = None  # Only include vector when explicitly requested
    
    class Config:
        from_attributes = True


class EmbeddingResultDTO(BaseModel):
    """DTO for embedding generation result"""
    embedding_id: UUID
    dataset_id: str
    row_id: str
    model_name: str
    dimension: int
    created_at: datetime
    status: str
    error_message: Optional[str] = None
    
    class Config:
        from_attributes = True


class DatasetDTO(BaseModel):
    """DTO for dataset data"""
    dataset_id: str
    name: str
    dimension: int
    embedding_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class GenerateEmbeddingRequestDTO(BaseModel):
    """DTO for generating a single embedding"""
    text: str
    dataset_id: str
    row_id: str
    model_name: str = "all-MiniLM-L6-v2"  # Default model


class BatchEmbeddingRequestDTO(BaseModel):
    """DTO for generating multiple embeddings"""
    texts: List[str]
    dataset_id: str
    row_ids: List[str]
    model_name: str = "all-MiniLM-L6-v2"  # Default model
    batch_size: int = 32  # Default batch size


class DeleteEmbeddingRequestDTO(BaseModel):
    """DTO for deleting an embedding"""
    embedding_id: UUID
    dataset_id: Optional[str] = None


class GetEmbeddingRequestDTO(BaseModel):
    """DTO for getting an embedding"""
    embedding_id: UUID
    dataset_id: Optional[str] = None
    include_vector: bool = False


class ListEmbeddingsRequestDTO(BaseModel):
    """DTO for listing embeddings"""
    dataset_id: str
    limit: int = 100
    offset: int = 0
    include_vectors: bool = False


class CreateDatasetRequestDTO(BaseModel):
    """DTO for creating a dataset"""
    name: str
    dimension: int = 384  # Default dimension for all-MiniLM-L6-v2
    metadata: Optional[Dict[str, Any]] = None


class ProcessDatasetRowsRequestDTO(BaseModel):
    """DTO for processing dataset rows"""
    dataset_id: str
    text_fields: Optional[List[str]] = None  # Fields to use for text, if None use all string fields
    row_ids: Optional[List[str]] = None  # If provided, only process these rows
    model_name: str = "all-MiniLM-L6-v2"  # Default model
    batch_size: int = 32  # Default batch size


class EmbeddingModelDTO(BaseModel):
    """DTO for embedding model data"""
    name: str
    dimension: int
    description: Optional[str] = None
    
    class Config:
        from_attributes = True 