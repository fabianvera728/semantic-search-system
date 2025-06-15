from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Any, Optional
from uuid import UUID

# Base class for all domain events
@dataclass
class DomainEvent:
    event_id: UUID
    timestamp: datetime
    event_type: str


@dataclass
class DatasetCreatedEvent(DomainEvent):
    dataset_id: UUID
    name: str
    description: str
    user_id: str
    row_count: int
    column_count: int
    tags: List[str]
    is_public: bool
    # Nueva funcionalidad para embeddings contextuales
    prompt_strategy: Optional[Dict[str, Any]] = None
    

@dataclass
class DatasetUpdatedEvent(DomainEvent):
    dataset_id: UUID
    name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    is_public: Optional[bool] = None


@dataclass
class DatasetRowsAddedEvent(DomainEvent):
    dataset_id: UUID
    row_count: int
    rows_data: List[Dict[str, Any]]
    # Nueva funcionalidad para embeddings contextuales
    prompt_strategy: Optional[Dict[str, Any]] = None


@dataclass
class DatasetColumnsAddedEvent(DomainEvent):
    dataset_id: UUID
    column_count: int
    columns_data: List[Dict[str, Any]] 