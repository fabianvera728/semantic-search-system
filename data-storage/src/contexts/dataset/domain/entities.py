from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Literal
from uuid import UUID, uuid4


@dataclass
class DatasetColumn:
    name: str
    type: Literal["string", "number", "boolean", "date", "object"]
    id: UUID = field(default_factory=uuid4)
    description: Optional[str] = None


@dataclass
class DatasetRow:
    data: Dict[str, Any]
    id: UUID = field(default_factory=uuid4)


@dataclass
class Dataset:
    name: str
    description: str
    user_id: str
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    row_count: int = 0
    column_count: int = 0
    tags: List[str] = field(default_factory=list)
    is_public: bool = False
    columns: List[DatasetColumn] = field(default_factory=list)
    rows: List[DatasetRow] = field(default_factory=list)

    def add_row(self, row: DatasetRow) -> None:
        """Add a row to the dataset and update the row count"""
        self.rows.append(row)
        self.row_count += 1
        self.updated_at = datetime.now()

    def add_column(self, column: DatasetColumn) -> None:
        """Add a column to the dataset and update the column count"""
        self.columns.append(column)
        self.column_count = len(self.columns)
        self.updated_at = datetime.now()

    def update_metadata(self, name: Optional[str] = None, description: Optional[str] = None, 
                        tags: Optional[List[str]] = None, is_public: Optional[bool] = None) -> None:
        """Update the dataset metadata"""
        if name is not None:
            self.name = name
        if description is not None:
            self.description = description
        if tags is not None:
            self.tags = tags
        if is_public is not None:
            self.is_public = is_public
        self.updated_at = datetime.now() 