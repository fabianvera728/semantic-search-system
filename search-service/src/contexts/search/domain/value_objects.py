from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Literal
from uuid import UUID, uuid4


@dataclass(frozen=True)
class SearchId:
    """Identificador único para una búsqueda"""
    value: UUID


@dataclass(frozen=True)
class SearchQuery:
    """Consulta de búsqueda"""
    text: str
    

@dataclass(frozen=True)
class DatasetId:
    """Identificador único para un dataset"""
    value: str


@dataclass(frozen=True)
class SearchConfig:
    """Configuración para una búsqueda"""
    limit: int = 10
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    search_type: Literal["semantic", "keyword", "hybrid"] = "semantic"
    hybrid_alpha: float = 0.5  # Peso para combinar búsqueda semántica y por palabras clave
    additional_params: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SearchRequest:
    """Solicitud de búsqueda"""
    query: SearchQuery
    dataset_id: DatasetId
    config: SearchConfig = field(default_factory=SearchConfig)
    search_id: SearchId = field(default_factory=lambda: SearchId(uuid4()))


@dataclass(frozen=True)
class EmbeddingRequest:
    """Solicitud para generar embeddings"""
    texts: List[str]
    model: str = "sentence-transformers/all-MiniLM-L6-v2"
    batch_size: int = 32
    request_id: UUID = field(default_factory=uuid4)
    additional_params: Dict[str, Any] = field(default_factory=dict) 