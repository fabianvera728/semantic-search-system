import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Integer, JSON, Index
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(AsyncAttrs, DeclarativeBase):
    pass


class Dataset(Base):
    __tablename__ = "datasets"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    row_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    column_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tags: Mapped[dict] = mapped_column(JSON, nullable=False, default=list)
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    prompt_strategy: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    columns: Mapped[List["DatasetColumn"]] = relationship("DatasetColumn", back_populates="dataset", cascade="all, delete-orphan")
    rows: Mapped[List["DatasetRow"]] = relationship("DatasetRow", back_populates="dataset", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Dataset(id={self.id}, name={self.name}, user_id={self.user_id})>"


class DatasetColumn(Base):
    __tablename__ = "dataset_columns"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id: Mapped[str] = mapped_column(String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    dataset: Mapped["Dataset"] = relationship("Dataset", back_populates="columns")
    
    def __repr__(self) -> str:
        return f"<DatasetColumn(id={self.id}, name={self.name}, type={self.type})>"


class DatasetRow(Base):
    __tablename__ = "dataset_rows"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id: Mapped[str] = mapped_column(String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    data: Mapped[dict] = mapped_column(JSON, nullable=False)
    
    dataset: Mapped["Dataset"] = relationship("Dataset", back_populates="rows")
    
    def __repr__(self) -> str:
        return f"<DatasetRow(id={self.id}, dataset_id={self.dataset_id})>" 