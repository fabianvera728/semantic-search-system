from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Literal
from uuid import UUID


@dataclass(frozen=True)
class DatasetId:
    value: UUID


@dataclass(frozen=True)
class UserId:
    value: str


@dataclass(frozen=True)
class CreateDatasetRequest:
    name: str
    description: str
    user_id: str
    tags: List[str]
    is_public: bool
    columns: List[Dict[str, Any]]
    rows: List[Dict[str, Any]]


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