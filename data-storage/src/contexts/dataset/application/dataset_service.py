from typing import List, Optional, Dict, Any
from uuid import UUID

from ..domain.entities import Dataset, DatasetColumn, DatasetRow
from ..domain.repositories import DatasetRepository
from ..domain.exceptions import DatasetNotFoundError, UnauthorizedAccessError
from ..domain.value_objects import (
    CreateDatasetRequest, 
    UpdateDatasetRequest,
    AddRowRequest,
    AddColumnRequest
)


class DatasetService:
    def __init__(self, repository: DatasetRepository):
        self.repository = repository

    async def create_dataset(self, request: CreateDatasetRequest) -> Dataset:
        """Create a new dataset"""
        # Create dataset entity
        dataset = Dataset(
            name=request.name,
            description=request.description,
            user_id=request.user_id,
            tags=request.tags,
            is_public=request.is_public
        )

        # Add columns
        for column_data in request.columns:
            column = DatasetColumn(
                name=column_data["name"],
                type=column_data["type"],
                description=column_data.get("description")
            )
            dataset.add_column(column)

        # Add rows
        for row_data in request.rows:
            row = DatasetRow(data=row_data)
            dataset.add_row(row)

        # Save to repository
        return await self.repository.save(dataset)

    async def get_dataset(self, dataset_id: UUID, user_id: Optional[str] = None) -> Dataset:
        """Get a dataset by ID"""
        dataset = await self.repository.find_by_id(dataset_id)
        
        if not dataset:
            raise DatasetNotFoundError(dataset_id)
        
        # Check access permissions
        if not dataset.is_public and user_id != dataset.user_id:
            raise UnauthorizedAccessError(user_id, dataset_id)
            
        return dataset

    async def update_dataset(self, request: UpdateDatasetRequest, user_id: str) -> Dataset:
        """Update a dataset"""
        dataset = await self.repository.find_by_id(request.dataset_id)
        
        if not dataset:
            raise DatasetNotFoundError(request.dataset_id)
        
        # Check ownership
        if user_id != dataset.user_id:
            raise UnauthorizedAccessError(user_id, request.dataset_id)
        
        # Update fields
        dataset.update_metadata(
            name=request.name,
            description=request.description,
            tags=request.tags,
            is_public=request.is_public
        )
        
        # Save changes
        return await self.repository.update(dataset)

    async def delete_dataset(self, dataset_id: UUID, user_id: str) -> bool:
        """Delete a dataset"""
        dataset = await self.repository.find_by_id(dataset_id)
        
        if not dataset:
            raise DatasetNotFoundError(dataset_id)
        
        # Check ownership
        if user_id != dataset.user_id:
            raise UnauthorizedAccessError(user_id, dataset_id)
        
        # Delete from repository
        return await self.repository.delete(dataset_id)

    async def list_datasets(self, limit: int = 100, offset: int = 0) -> List[Dataset]:
        """List all datasets with pagination"""
        return await self.repository.find_all(limit, offset)

    async def list_user_datasets(self, user_id: str, limit: int = 100, offset: int = 0) -> List[Dataset]:
        """List all datasets for a specific user"""
        return await self.repository.find_by_user_id(user_id, limit, offset)

    async def list_public_datasets(self, limit: int = 100, offset: int = 0) -> List[Dataset]:
        """List all public datasets"""
        return await self.repository.find_public(limit, offset)

    async def add_row(self, request: AddRowRequest, user_id: str) -> Dataset:
        """Add a row to a dataset"""
        dataset = await self.repository.find_by_id(request.dataset_id)
        
        if not dataset:
            raise DatasetNotFoundError(request.dataset_id)
        
        # Check ownership
        if user_id != dataset.user_id:
            raise UnauthorizedAccessError(user_id, request.dataset_id)
        
        # Add row
        row = DatasetRow(data=request.data)
        dataset.add_row(row)
        
        # Save changes
        return await self.repository.update(dataset)

    async def add_column(self, request: AddColumnRequest, user_id: str) -> Dataset:
        """Add a column to a dataset"""
        dataset = await self.repository.find_by_id(request.dataset_id)
        
        if not dataset:
            raise DatasetNotFoundError(request.dataset_id)
        
        # Check ownership
        if user_id != dataset.user_id:
            raise UnauthorizedAccessError(user_id, request.dataset_id)
        
        # Add column
        column = DatasetColumn(
            name=request.name,
            type=request.type,
            description=request.description
        )
        dataset.add_column(column)
        
        # Save changes
        return await self.repository.update(dataset) 