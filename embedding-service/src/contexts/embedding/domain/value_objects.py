from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional, Literal
from uuid import UUID, uuid4


@dataclass(frozen=True)
class EmbeddingId:
    value: UUID


@dataclass(frozen=True)
class DatasetId:
    value: str


@dataclass(frozen=True)
class RowId:
    value: str


@dataclass(frozen=True)
class TextContent:
    value: str
    field_name: str = ""


@dataclass(frozen=True)
class ModelName:
    value: str


@dataclass(frozen=True)
class GenerateEmbeddingRequest:
    text: str
    dataset_id: str
    row_id: str
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    batch_id: Optional[UUID] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class BatchEmbeddingRequest:
    texts: List[str]
    dataset_id: str
    row_ids: List[str]
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    batch_size: int = 32
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DeleteEmbeddingRequest:
    embedding_id: UUID
    dataset_id: str


@dataclass(frozen=True)
class GetEmbeddingRequest:
    embedding_id: UUID
    dataset_id: str


@dataclass(frozen=True)
class ListEmbeddingsRequest:
    dataset_id: str
    limit: int = 100
    offset: int = 0
    filter_criteria: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CreateDatasetRequest:
    dataset_id: str
    name: str
    dimension: int = 384
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ProcessDatasetRowsRequest:
    dataset_id: str
    rows: Optional[List[Dict[str, Any]]] = None
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    text_fields: Optional[List[str]] = None
    batch_size: int = 32
    force_refresh: bool = False


@dataclass(frozen=True)
class EmbeddingResult:
    embedding_id: UUID
    dataset_id: str
    row_id: str
    model_name: str
    dimension: int
    created_at: datetime = field(default_factory=datetime.now)
    status: Literal["success", "error"] = "success"
    error_message: str = "" 