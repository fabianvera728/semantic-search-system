from typing import List, Dict, Any, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Request
from pydantic import BaseModel, Field

from ...contexts.dataset.application import DatasetService
from ...contexts.dataset.domain.exceptions import DatasetNotFoundError, UnauthorizedAccessError
from ...contexts.dataset.domain.value_objects import (
    CreateDatasetRequest, 
    UpdateDatasetRequest,
    AddRowRequest,
    AddColumnRequest,
    GetDatasetRowsRequest
)
from ...middleware import get_current_user_id
import logging
logger = logging.getLogger(__name__)

# Función auxiliar para obtener user_id con fallback
async def get_user_id_optional() -> str:
    """Obtiene el user_id del token JWT, o usa un valor por defecto si no hay autenticación."""
    try:
        return await get_current_user_id()
    except Exception:
        # Si no hay autenticación, usar un user_id por defecto para servicios internos
        return "system-service"


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


class GetDatasetRowRequest(BaseModel):
    dataset_id: UUID
    row_id: UUID


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
    rows: List[DatasetRowSchema] = []

    class Config:
        from_attributes = True


class DatasetRowsSchema(BaseModel):
    rows: List[Dict[str, Any]]
    total: int
    limit: int
    offset: int


class PaginationParams(BaseModel):
    limit: int = Query(100, ge=1, le=1000)
    offset: int = Query(0, ge=0)


# Schemas para Embeddings Contextuales
class EmbeddingPromptTemplateSchema(BaseModel):
    template: str
    description: str
    field_mappings: Dict[str, str] = {}
    metadata: Dict[str, Any] = {}


class EmbeddingPromptStrategySchema(BaseModel):
    strategy_type: str  # "concatenate", "simple_prompt", "template"
    simple_prompt: Optional[str] = None
    prompt_template: Optional[EmbeddingPromptTemplateSchema] = None


class CreateDatasetSchema(BaseModel):
    name: str
    description: str
    tags: List[str]
    is_public: bool
    columns: List[Dict[str, Any]]
    rows: List[Dict[str, Any]]
    # Nueva funcionalidad para prompts contextuales
    prompt_strategy: Optional[EmbeddingPromptStrategySchema] = None


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
                # Convertir prompt strategy si existe
                prompt_strategy = None
                if dataset.prompt_strategy:
                    prompt_strategy = self._convert_prompt_strategy_schema_to_domain(dataset.prompt_strategy)
                
                request = CreateDatasetRequest(
                    name=dataset.name,
                    description=dataset.description,
                    user_id=user_id,
                    tags=dataset.tags,
                    is_public=dataset.is_public,
                    columns=dataset.columns,
                    rows=dataset.rows,
                    prompt_strategy=prompt_strategy
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
            user_id: str = Depends(get_user_id_optional)
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
                
        @self.router.get("/{dataset_id}/rows", response_model=DatasetRowsSchema)
        async def get_dataset_rows(
            dataset_id: UUID = Path(...),
            limit: int = Query(100, ge=1, le=1000),
            offset: int = Query(0, ge=0),
            user_id: str = Depends(get_current_user_id)
        ):
            try:
                request = GetDatasetRowsRequest(
                    dataset_id=dataset_id,
                    limit=limit,
                    offset=offset
                )
                
                dataset = await self.dataset_service.get_dataset(dataset_id, user_id)
                rows = await self.dataset_service.get_dataset_rows(request, user_id)
                
                return {
                    "rows": rows,
                    "total": dataset.row_count,
                    "limit": limit,
                    "offset": offset
                }
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
            
        @self.router.get("/{dataset_id}/rows/{row_id}", response_model=DatasetRowSchema)
        async def get_dataset_row(
            dataset_id: UUID = Path(...),
            row_id: UUID = Path(...)
        ):
            try:
                request = GetDatasetRowRequest(
                    dataset_id=dataset_id,
                    row_id=row_id
                )
                
                row = await self.dataset_service.get_dataset_row(request)
                
                return {
                    "id": row.id,
                    "data": row.data
                }
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
            user_id: str = Depends(get_user_id_optional)
        ):
            logger.info(f"🔍 ADD_ROW - Inicio: dataset_id={dataset_id}, user_id={user_id}")
            logger.info(f"🔍 ADD_ROW - Datos recibidos: {row.data}")
            logger.info(f"🔍 ADD_ROW - Tipo de datos: {type(row.data)}")
            
            try:
                request = AddRowRequest(
                    dataset_id=dataset_id,
                    data=row.data
                )
                logger.info(f"🔍 ADD_ROW - Request creado: dataset_id={request.dataset_id}")
                logger.info(f"🔍 ADD_ROW - Request data: {request.data}")
                
                result = await self.dataset_service.add_row(request, user_id)
                logger.info(f"🔍 ADD_ROW - Resultado exitoso: dataset_id={result.id}, row_count={result.row_count}")
                
                return self._entity_to_detail_schema(result)
            except DatasetNotFoundError as e:
                logger.error(f"❌ ADD_ROW - Dataset not found: {e}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Dataset with ID {dataset_id} not found"
                )
            except UnauthorizedAccessError as e:
                logger.error(f"❌ ADD_ROW - Unauthorized: {e}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"You don't have permission to modify this dataset"
                )
            except Exception as e:
                logger.error(f"❌ ADD_ROW - Error interno: {type(e).__name__}: {str(e)}")
                logger.error(f"❌ ADD_ROW - Dataset ID: {dataset_id}")
                logger.error(f"❌ ADD_ROW - User ID: {user_id}")
                logger.error(f"❌ ADD_ROW - Row data: {row.data}")
                import traceback
                logger.error(f"❌ ADD_ROW - Traceback: {traceback.format_exc()}")
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
        base_schema = self._entity_to_schema(dataset)
        
        base_schema["columns"] = [
            {
                "id": str(column.id),
                "name": column.name,
                "type": column.type,
                "description": column.description
            }
            for column in dataset.columns
        ]

        base_schema["rows"] = []
        
        return base_schema
    
    def _convert_prompt_strategy_schema_to_domain(self, schema: EmbeddingPromptStrategySchema):
        """Convierte EmbeddingPromptStrategySchema a domain object"""
        from ...contexts.dataset.domain.value_objects import EmbeddingPromptStrategy, EmbeddingPromptTemplate
        
        prompt_template = None
        if schema.prompt_template:
            prompt_template = EmbeddingPromptTemplate(
                template=schema.prompt_template.template,
                description=schema.prompt_template.description,
                field_mappings=schema.prompt_template.field_mappings,
                metadata=schema.prompt_template.metadata
            )
        
        return EmbeddingPromptStrategy(
            strategy_type=schema.strategy_type,
            simple_prompt=schema.simple_prompt,
            prompt_template=prompt_template
        ) 