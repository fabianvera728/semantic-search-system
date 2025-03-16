from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Literal
from uuid import UUID, uuid4


@dataclass
class DatasetColumn:
    id: UUID = field(default_factory=uuid4)
    name: str
    type: Literal["string", "number", "boolean", "date", "object"]
    description: Optional[str] = None


@dataclass
class DatasetRow:
    id: UUID = field(default_factory=uuid4)
    data: Dict[str, Any]


@dataclass
class Dataset:
    id: UUID = field(default_factory=uuid4)
    name: str
    description: str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    user_id: str
    row_count: int = 0
    column_count: int = 0
    tags: List[str] = field(default_factory=list)
    is_public: bool = False
    columns: List[DatasetColumn] = field(default_factory=list)
    rows: List[DatasetRow] = field(default_factory=list)

    def add_row(self, row: DatasetRow) -> None:
        self.rows.append(row)
        self.row_count = len(self.rows)
        self.updated_at = datetime.now()

    def add_column(self, column: DatasetColumn) -> None:
        self.columns.append(column)
        self.column_count = len(self.columns)
        self.updated_at = datetime.now()

    def update_metadata(self, name: Optional[str] = None, description: Optional[str] = None, 
                        tags: Optional[List[str]] = None, is_public: Optional[bool] = None) -> None:
        if name is not None:
            self.name = name
        if description is not None:
            self.description = description
        if tags is not None:
            self.tags = tags
        if is_public is not None:
            self.is_public = is_public
        self.updated_at = datetime.now() 