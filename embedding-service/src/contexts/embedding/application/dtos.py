from typing import List, Dict, Any, Optional, Literal
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class EmbeddingPromptTemplateDTO(BaseModel):
    """DTO para template de prompts contextuales"""
    template: str
    description: str
    field_mappings: Optional[Dict[str, str]] = None
    metadata: Optional[Dict[str, Any]] = None


class EmbeddingPromptStrategyDTO(BaseModel):
    """DTO para estrategia de generación de contenido contextual"""
    strategy_type: Literal["concatenate", "simple_prompt", "template"] = "concatenate"
    simple_prompt: Optional[str] = None
    prompt_template: Optional[EmbeddingPromptTemplateDTO] = None


class EmbeddingDTO(BaseModel):
    embedding_id: UUID
    dataset_id: str
    row_id: str
    model_name: str
    dimension: int
    text: str
    created_at: datetime
    vector: Optional[List[float]] = None
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class EmbeddingResultDTO(BaseModel):
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
    text: str
    dataset_id: str
    row_id: str
    model_name: str = "paraphrase-multilingual-MiniLM-L12-v2" 


class BatchEmbeddingRequestDTO(BaseModel):
    texts: List[str]
    dataset_id: str
    row_ids: List[str]
    model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"
    batch_size: int = 32


class DeleteEmbeddingRequestDTO(BaseModel):
    embedding_id: UUID
    dataset_id: Optional[str] = None


class GetEmbeddingRequestDTO(BaseModel):
    embedding_id: UUID
    dataset_id: Optional[str] = None
    include_vector: bool = False


class ListEmbeddingsRequestDTO(BaseModel):
    dataset_id: str
    limit: int = 100
    offset: int = 0
    include_vectors: bool = False


class CreateDatasetRequestDTO(BaseModel):
    name: str
    dataset_id: Optional[str] = None 
    dimension: int = 384
    metadata: Optional[Dict[str, Any]] = None

class ProcessDatasetRowsRequestDTO(BaseModel):
    dataset_id: str
    text_fields: Optional[List[str]] = None
    model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"    
    rows: Optional[List[Dict[str, Any]]] = None
    batch_size: int = 32
    # Nueva funcionalidad para prompts contextuales
    prompt_strategy: Optional[EmbeddingPromptStrategyDTO] = None


class EmbeddingModelDTO(BaseModel):
    name: str
    dimension: int
    description: Optional[str] = None
    
    class Config:
        from_attributes = True 