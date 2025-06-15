from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Literal
from uuid import UUID


@dataclass(frozen=True)
class DatasetId:
    value: UUID


@dataclass(frozen=True)
class UserId:
    value: str


# Value Objects para Embeddings Contextuales
@dataclass(frozen=True)
class EmbeddingPromptTemplate:
    """Template para generar texto contextualizado para embeddings"""
    template: str
    description: str
    field_mappings: Dict[str, str]
    metadata: Dict[str, Any]


@dataclass(frozen=True)
class EmbeddingPromptStrategy:
    """Estrategia para generar contenido contextualizado"""
    strategy_type: Literal["concatenate", "simple_prompt", "template"]
    simple_prompt: Optional[str] = None
    prompt_template: Optional[EmbeddingPromptTemplate] = None


@dataclass(frozen=True)
class CreateDatasetRequest:
    name: str
    description: str
    user_id: str
    tags: List[str]
    is_public: bool
    columns: List[Dict[str, Any]]
    rows: List[Dict[str, Any]]
    # Nueva funcionalidad para prompts contextuales
    prompt_strategy: Optional[EmbeddingPromptStrategy] = None


@dataclass(frozen=True)
class UpdateDatasetRequest:
    dataset_id: UUID
    name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    is_public: Optional[bool] = None


@dataclass(frozen=True)
class AddRowRequest:
    dataset_id: UUID
    data: Dict[str, Any]


@dataclass(frozen=True)
class AddColumnRequest:
    dataset_id: UUID
    name: str
    type: Literal["string", "number", "boolean", "date", "object"]
    description: Optional[str] = None


@dataclass(frozen=True)
class GetDatasetRowsRequest:
    dataset_id: UUID
    limit: int = 100
    offset: int = 0 


@dataclass(frozen=True)
class GetDatasetRowRequest:
    dataset_id: UUID
    row_id: UUID
