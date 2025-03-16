from typing import List, Dict, Any, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from pydantic import BaseModel, Field

from ...contexts.dataset.application import DatasetService
from ...contexts.dataset.domain.exceptions import DatasetNotFoundError, UnauthorizedAccessError
from ...contexts.dataset.domain.value_objects import (
    CreateDatasetRequest, 
    UpdateDatasetRequest,
    AddRowRequest,
    AddColumnRequest
)


# Pydantic models for API requests and responses
class DatasetColumnSchema(BaseModel):
    id: str
    name: str
    type: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


class DatasetRowSchema(BaseModel):
    id: str
    data: Dict[str, Any]

    class Config:
        from_attributes = True


class DatasetSchema(BaseModel):
    id: str
    name: str
    description: str
    created_at: str
    updated_at: str
    user_id: str
    row_count: int
    column_count: int
    tags: List[str]
    is_public: bool

    class Config:
        from_attributes = True


class DatasetDetailSchema(DatasetSchema):
    columns: List[DatasetColumnSchema]
    rows: List[DatasetRowSchema]

    class Config:
        from_attributes = True


class CreateDatasetSchema(BaseModel):
    name: str
    description: str
    tags: List[str]
    is_public: bool
    columns: List[Dict[str, Any]]
    rows: List[Dict[str, Any]]


class UpdateDatasetSchema(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    is_public: Optional[bool] = None


class AddRowSchema(BaseModel):
    data: Dict[str, Any]


class AddColumnSchema(BaseModel):
    name: str
    type: str
    description: Optional[str] = None


# Dependency for getting the current user ID (to be replaced with actual auth)
async def get_current_user_id() -> str:
    # This is a placeholder. In a real app, this would extract the user ID from a token
    return "test-user-id"


class DatasetController:
    def __init__(self, dataset_service: DatasetService):
        self.dataset_service = dataset_service
        self.router = APIRouter(prefix="/datasets", tags=["datasets"])
        self._register_routes()

    def _register_routes(self):
        @self.router.post("", response_model=DatasetSchema, status_code=status.HTTP_201_CREATED)
        async def create_dataset(
            dataset: CreateDatasetSchema,
            user_id: str = Depends(get_current_user_id)
        ):
            try:
                request = CreateDatasetRequest(
                    name=dataset.name,
                    description=dataset.description,
                    user_id=user_id,
                    tags=dataset.tags,
                    is_public=dataset.is_public,
                    columns=dataset.columns,
                    rows=dataset.rows
                )
                result = await self.dataset_service.create_dataset(request)
                return self._entity_to_schema(result)
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=str(e)
                )

        @self.router.get("", response_model=List[DatasetSchema])
        async def list_datasets(
            limit: int = Query(100, ge=1, le=1000),
            offset: int = Query(0, ge=0),
            user_id: str = Depends(get_current_user_id)
        ):
            try:
                datasets = await self.dataset_service.list_user_datasets(user_id, limit, offset)
                return [self._entity_to_schema(dataset) for dataset in datasets]
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=str(e)
                )

        @self.router.get("/public", response_model=List[DatasetSchema])
        async def list_public_datasets(
            limit: int = Query(100, ge=1, le=1000),
            offset: int = Query(0, ge=0)
        ):
            try:
                datasets = await self.dataset_service.list_public_datasets(limit, offset)
                return [self._entity_to_schema(dataset) for dataset in datasets]
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=str(e)
                )

        @self.router.get("/{dataset_id}", response_model=DatasetDetailSchema)
        async def get_dataset(
            dataset_id: UUID = Path(...),
            user_id: str = Depends(get_current_user_id)
        ):
            try:
                dataset = await self.dataset_service.get_dataset(dataset_id, user_id)
                return self._entity_to_detail_schema(dataset)
            except DatasetNotFoundError:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Dataset with ID {dataset_id} not found"
                )
            except UnauthorizedAccessError:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"You don't have permission to access this dataset"
                )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=str(e)
                )

        @self.router.put("/{dataset_id}", response_model=DatasetSchema)
        async def update_dataset(
            dataset: UpdateDatasetSchema,
            dataset_id: UUID = Path(...),
            user_id: str = Depends(get_current_user_id)
        ):
            try:
                request = UpdateDatasetRequest(
                    dataset_id=dataset_id,
                    name=dataset.name,
                    description=dataset.description,
                    tags=dataset.tags,
                    is_public=dataset.is_public
                )
                result = await self.dataset_service.update_dataset(request, user_id)
                return self._entity_to_schema(result)
            except DatasetNotFoundError:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Dataset with ID {dataset_id} not found"
                )
            except UnauthorizedAccessError:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"You don't have permission to update this dataset"
                )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=str(e)
                )

        @self.router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
        async def delete_dataset(
            dataset_id: UUID = Path(...),
            user_id: str = Depends(get_current_user_id)
        ):
            try:
                await self.dataset_service.delete_dataset(dataset_id, user_id)
                return None
            except DatasetNotFoundError:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Dataset with ID {dataset_id} not found"
                )
            except UnauthorizedAccessError:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"You don't have permission to delete this dataset"
                )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=str(e)
                )

        @self.router.post("/{dataset_id}/rows", response_model=DatasetDetailSchema)
        async def add_row(
            row: AddRowSchema,
            dataset_id: UUID = Path(...),
            user_id: str = Depends(get_current_user_id)
        ):
            try:
                request = AddRowRequest(
                    dataset_id=dataset_id,
                    data=row.data
                )
                result = await self.dataset_service.add_row(request, user_id)
                return self._entity_to_detail_schema(result)
            except DatasetNotFoundError:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Dataset with ID {dataset_id} not found"
                )
            except UnauthorizedAccessError:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"You don't have permission to modify this dataset"
                )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=str(e)
                )

        @self.router.post("/{dataset_id}/columns", response_model=DatasetDetailSchema)
        async def add_column(
            column: AddColumnSchema,
            dataset_id: UUID = Path(...),
            user_id: str = Depends(get_current_user_id)
        ):
            try:
                request = AddColumnRequest(
                    dataset_id=dataset_id,
                    name=column.name,
                    type=column.type,
                    description=column.description
                )
                result = await self.dataset_service.add_column(request, user_id)
                return self._entity_to_detail_schema(result)
            except DatasetNotFoundError:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Dataset with ID {dataset_id} not found"
                )
            except UnauthorizedAccessError:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"You don't have permission to modify this dataset"
                )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=str(e)
                )

    def _entity_to_schema(self, dataset):
        """Convert a Dataset entity to a DatasetSchema"""
        return {
            "id": str(dataset.id),
            "name": dataset.name,
            "description": dataset.description,
            "created_at": dataset.created_at.isoformat(),
            "updated_at": dataset.updated_at.isoformat(),
            "user_id": dataset.user_id,
            "row_count": dataset.row_count,
            "column_count": dataset.column_count,
            "tags": dataset.tags,
            "is_public": dataset.is_public
        }

    def _entity_to_detail_schema(self, dataset):
        """Convert a Dataset entity to a DatasetDetailSchema"""
        base_schema = self._entity_to_schema(dataset)
        
        # Add columns and rows
        base_schema["columns"] = [
            {
                "id": str(column.id),
                "name": column.name,
                "type": column.type,
                "description": column.description
            }
            for column in dataset.columns
        ]
        
        base_schema["rows"] = [
            {
                "id": str(row.id),
                "data": row.data
            }
            for row in dataset.rows
        ]
        
        return base_schema 