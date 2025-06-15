from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime

from ..domain.entities import Dataset, DatasetColumn, DatasetRow
from ..domain.repositories import DatasetRepository
from ..domain.exceptions import DatasetNotFoundError, UnauthorizedAccessError
from ..domain.value_objects import (
    CreateDatasetRequest, 
    UpdateDatasetRequest,
    AddRowRequest,
    AddColumnRequest,
    GetDatasetRowsRequest,
    GetDatasetRowRequest
)
from ..domain.events import (
    DatasetCreatedEvent,
    DatasetUpdatedEvent,
    DatasetRowsAddedEvent,
    DatasetColumnsAddedEvent
)

from ....infrastructure.events import get_event_bus
import logging
logger = logging.getLogger(__name__)


class DatasetService:
    def __init__(self, repository: DatasetRepository):
        self.repository = repository
        self.event_bus = get_event_bus()

    async def create_dataset(self, request: CreateDatasetRequest) -> Dataset:
        dataset = Dataset(
            name=request.name,
            description=request.description,
            user_id=request.user_id,
            tags=request.tags,
            is_public=request.is_public
        )

        for column_data in request.columns:
            column = DatasetColumn(
                name=column_data["name"],
                type=column_data["type"],
                description=column_data.get("description")
            )
            dataset.add_column(column)

        for row_data in request.rows:
            row = DatasetRow(data=row_data)
            dataset.add_row(row)

        saved_dataset = await self.repository.save(dataset)
        
        # Convertir prompt strategy a dict si existe
        prompt_strategy_dict = None
        if request.prompt_strategy:
            prompt_strategy_dict = self._convert_prompt_strategy_to_dict(request.prompt_strategy)
        
        await self._publish_dataset_created_event(saved_dataset, prompt_strategy_dict)
        
        row_data_with_ids = []
        for i, saved_row in enumerate(saved_dataset.rows):
            if i >= len(request.rows):
                continue

            row_data = request.rows[i].copy()
            row_data["id"] = str(saved_row.id)
            row_data_with_ids.append(row_data)

        if request.rows and len(request.rows) > 0:
            await self._publish_rows_added_event(
                saved_dataset,
                row_data_with_ids,
                prompt_strategy_dict
            )
        
        return saved_dataset

    async def get_dataset(
        self,
        dataset_id: UUID,
        user_id: Optional[str] = None
    ) -> Dataset:
        dataset = await self.repository.find_by_id(dataset_id)
        if not dataset:
            raise DatasetNotFoundError(dataset_id)

        if not dataset.is_public and user_id and user_id != dataset.user_id:
            raise UnauthorizedAccessError()

        return dataset

    async def get_dataset_rows(
        self,
        request: GetDatasetRowsRequest,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        dataset = await self.get_dataset(request.dataset_id, user_id)
        
        rows = await self.repository.get_dataset_rows(
            dataset_id=request.dataset_id,
            limit=request.limit,
            offset=request.offset
        )
        
        return rows
    
    async def get_dataset_row(
        self,
        request: GetDatasetRowRequest,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        dataset = await self.get_dataset(request.dataset_id, user_id)

        row = await self.repository.get_dataset_row(
            dataset_id=request.dataset_id,
            row_id=request.row_id
        )

        return row

    async def update_dataset(self, request: UpdateDatasetRequest, user_id: str) -> Dataset:
        dataset = await self.repository.find_by_id(request.dataset_id)
        if not dataset:
            raise DatasetNotFoundError(request.dataset_id)

        if dataset.user_id != user_id:
            raise UnauthorizedAccessError()

        dataset.update_metadata(
            name=request.name,
            description=request.description,
            tags=request.tags,
            is_public=request.is_public
        )

        updated_dataset = await self.repository.save(dataset)
        
        # Publicar evento de dataset actualizado
        await self._publish_dataset_updated_event(updated_dataset, request)
        
        return updated_dataset

    async def delete_dataset(self, dataset_id: UUID, user_id: str) -> bool:
        dataset = await self.repository.find_by_id(dataset_id)
        if not dataset:
            raise DatasetNotFoundError(dataset_id)

        if dataset.user_id != user_id:
            raise UnauthorizedAccessError()

        return await self.repository.delete(dataset_id)

    async def list_datasets(self, limit: int = 100, offset: int = 0) -> List[Dataset]:
        return await self.repository.find_all(limit, offset)

    async def list_user_datasets(
        self,
        user_id: str,
        limit: int = 100, 
        offset: int = 0
    ) -> List[Dataset]:
        return await self.repository.find_by_user_id(
            user_id=user_id,
            limit=limit,
            offset=offset
        )

    async def list_public_datasets(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dataset]:
        return await self.repository.find_public(
            limit=limit,
            offset=offset
        )

    async def add_row(self, request: AddRowRequest, user_id: str) -> Dataset:
        dataset = await self.repository.find_by_id(request.dataset_id)
        if not dataset:
            raise DatasetNotFoundError(request.dataset_id)

        if dataset.user_id != user_id:
            raise UnauthorizedAccessError()

        row = DatasetRow(data=request.data)
        dataset.add_row(row)

        updated_dataset = await self.repository.save(dataset)
        
        # Publicar evento de filas añadidas
        # Para add_row individual, no tenemos prompt_strategy disponible, usar None
        await self._publish_rows_added_event(updated_dataset, [request.data], None)
        
        return updated_dataset

    async def add_column(self, request: AddColumnRequest, user_id: str) -> Dataset:
        dataset = await self.repository.find_by_id(request.dataset_id)
        if not dataset:
            raise DatasetNotFoundError(request.dataset_id)

        if dataset.user_id != user_id:
            raise UnauthorizedAccessError()

        column = DatasetColumn(
            name=request.name,
            type=request.type,
            description=request.description
        )
        dataset.add_column(column)

        updated_dataset = await self.repository.save(dataset)
        
        # Publicar evento de columnas añadidas
        await self._publish_columns_added_event(updated_dataset, [
            {"name": request.name, "type": request.type, "description": request.description}
        ])
        
        return updated_dataset
    
    # Métodos privados para conversión de datos
    
    def _convert_prompt_strategy_to_dict(self, prompt_strategy) -> Dict[str, Any]:
        """Convierte EmbeddingPromptStrategy a dict para serialización"""
        result = {
            "strategy_type": prompt_strategy.strategy_type
        }
        
        if prompt_strategy.simple_prompt:
            result["simple_prompt"] = prompt_strategy.simple_prompt
            
        if prompt_strategy.prompt_template:
            result["prompt_template"] = {
                "template": prompt_strategy.prompt_template.template,
                "description": prompt_strategy.prompt_template.description,
                "field_mappings": prompt_strategy.prompt_template.field_mappings,
                "metadata": prompt_strategy.prompt_template.metadata
            }
            
        return result
    
    # Métodos privados para publicar eventos
    
    async def _publish_dataset_created_event(self, dataset: Dataset, prompt_strategy: Optional[Dict[str, Any]] = None) -> None:
        """Publica un evento cuando se crea un dataset"""
        event = DatasetCreatedEvent(
            event_id=uuid4(),
            timestamp=datetime.now(),
            event_type="dataset.created",
            dataset_id=dataset.id,
            name=dataset.name,
            description=dataset.description,
            user_id=dataset.user_id,
            row_count=dataset.row_count,
            column_count=dataset.column_count,
            tags=dataset.tags,
            is_public=dataset.is_public,
            prompt_strategy=prompt_strategy
        )
        
        await self.event_bus.publish(event)
        logger.info(f"Published dataset.created event for dataset {dataset.id} with prompt_strategy: {bool(prompt_strategy)}")
        
    async def _publish_dataset_updated_event(self, dataset: Dataset, request: UpdateDatasetRequest) -> None:
        """Publica un evento cuando se actualiza un dataset"""
        event = DatasetUpdatedEvent(
            event_id=uuid4(),
            timestamp=datetime.now(),
            event_type="dataset.updated",
            dataset_id=dataset.id,
            name=request.name,
            description=request.description,
            tags=request.tags,
            is_public=request.is_public
        )
        
        await self.event_bus.publish(event)
        logger.info(f"Published dataset.updated event for dataset {dataset.id}")
        
    async def _publish_rows_added_event(self, dataset: Dataset, rows_data: List[Dict[str, Any]], prompt_strategy: Optional[Dict[str, Any]] = None) -> None:
        """Publica un evento cuando se añaden filas a un dataset"""
        event = DatasetRowsAddedEvent(
            event_id=uuid4(),
            timestamp=datetime.now(),
            event_type="dataset.rows_added",
            dataset_id=dataset.id,
            row_count=len(rows_data),
            rows_data=rows_data,
            prompt_strategy=prompt_strategy
        )
        
        await self.event_bus.publish(event)
        logger.info(f"Published dataset.rows_added event for dataset {dataset.id} with prompt_strategy: {bool(prompt_strategy)}")
        
    async def _publish_columns_added_event(self, dataset: Dataset, columns_data: List[Dict[str, Any]]) -> None:
        """Publica un evento cuando se añaden columnas a un dataset"""
        event = DatasetColumnsAddedEvent(
            event_id=uuid4(),
            timestamp=datetime.now(),
            event_type="dataset.columns_added",
            dataset_id=dataset.id,
            column_count=len(columns_data),
            columns_data=columns_data
        )
        
        await self.event_bus.publish(event)
        logger.info(f"Published dataset.columns_added event for dataset {dataset.id}") 
