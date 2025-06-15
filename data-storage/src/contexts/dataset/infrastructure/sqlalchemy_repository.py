import json
import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
import copy

from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.db import Dataset as DatasetModel, DatasetColumn as DatasetColumnModel, DatasetRow as DatasetRowModel
from ..domain.entities import Dataset, DatasetColumn, DatasetRow
from ..domain.repositories import DatasetRepository
from src.infrastructure.db.database import db


logger = logging.getLogger(__name__)


class SQLAlchemyDatasetRepository(DatasetRepository):
    
    def __init__(self):
        logger.info("Repositorio SQLAlchemy de datasets inicializado")

    def _get_session(self) -> AsyncSession:
        return db.get_session()
    
    async def save(self, dataset: Dataset) -> Dataset: 
        async with self._get_session() as session:
            try:
                dataset_model = DatasetModel(
                    id=str(dataset.id),
                    name=dataset.name,
                    description=dataset.description,
                    created_at=dataset.created_at,
                    updated_at=dataset.updated_at,
                    user_id=dataset.user_id,
                    row_count=dataset.row_count,
                    column_count=dataset.column_count,
                    tags=dataset.tags,
                    is_public=dataset.is_public,
                    prompt_strategy=dataset.prompt_strategy
                )
                
                session.add(dataset_model)
                await session.flush()
                for i, column in enumerate(dataset.columns):
                    column_model = DatasetColumnModel(
                        id=str(column.id),
                        dataset_id=str(dataset.id),
                        name=column.name,
                        type=column.type,
                        description=column.description
                    )
                    session.add(column_model)
                
                for i, row in enumerate(dataset.rows):
                    row_model = DatasetRowModel(
                        id=str(row.id),
                        dataset_id=str(dataset.id),
                        data=row.data
                    )
                    session.add(row_model)
                
                await session.commit()
                
                return copy.deepcopy(dataset)
            except Exception as e:
                await session.rollback()
                raise
    
    async def find_by_id(self, dataset_id: UUID) -> Optional[Dataset]:
        async with self._get_session() as session:
            stmt = select(DatasetModel).where(DatasetModel.id == str(dataset_id))
            result = await session.execute(stmt)
            dataset_model = result.scalar_one_or_none()
            
            if not dataset_model:
                return None
            
            return await self._model_to_entity_with_relations(dataset_model, session)
    
    async def find_by_user_id(self, user_id: str, limit: int = 100, offset: int = 0) -> List[Dataset]:
        async with self._get_session() as session:
            try: 
                stmt = select(DatasetModel).where(DatasetModel.user_id == user_id).offset(offset).limit(limit)
                result = await session.execute(stmt)
                dataset_models = result.scalars().all()

                return [
                    await self._model_to_entity_with_relations(model, session) 
                    for model in dataset_models
                ]
            except Exception as e:
                raise
    
    async def find_public(self, limit: int = 100, offset: int = 0) -> List[Dataset]:
        async with self._get_session() as session:
            stmt = select(DatasetModel).where(DatasetModel.is_public == True).offset(offset).limit(limit)
            result = await session.execute(stmt)
            dataset_models = result.scalars().all()
            
            return [await self._model_to_entity_with_relations(model, session) for model in dataset_models]
    
    async def find_all(self, limit: int = 100, offset: int = 0) -> List[Dataset]:        
        async with self._get_session() as session:
            try:
                stmt = select(DatasetModel).offset(offset).limit(limit)
                result = await session.execute(stmt)
                dataset_models = result.scalars().all()
                
                detailed_datasets = []
                for model in dataset_models:
                    entity = await self._model_to_entity_with_relations(model, session)
                    detailed_datasets.append(entity)
                
                return detailed_datasets
            except Exception as e:
                raise
    
    async def get_dataset_rows(self, dataset_id: UUID, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get paginated rows for a specific dataset"""
        async with self._get_session() as session:
            try:
                # Query rows with pagination
                stmt = (
                    select(DatasetRowModel)
                    .where(DatasetRowModel.dataset_id == str(dataset_id))
                    .offset(offset)
                    .limit(limit)
                )
                result = await session.execute(stmt)
                row_models = result.scalars().all()
                
                # Convert models to dicts
                return [row_model.data for row_model in row_models]
            except Exception as e:
                logger.error(f"Error fetching dataset rows: {str(e)}")
                raise

    async def get_dataset_row(self, dataset_id: UUID, row_id: UUID) -> Dict[str, Any]:
        async with self._get_session() as session:
            try:
                stmt = select(DatasetRowModel).where(DatasetRowModel.id == str(row_id))
                result = await session.execute(stmt)
                row_model = result.scalar_one_or_none()

                if not row_model:
                    raise ValueError(f"Row with ID {row_id} not found")
                
                return row_model
            except Exception as e:
                raise
    
    
    async def update(self, dataset: Dataset) -> Dataset:        
        async with self._get_session() as session:
            stmt = select(DatasetModel).where(DatasetModel.id == str(dataset.id))
            result = await session.execute(stmt)
            dataset_model = result.scalar_one_or_none()
            
            if not dataset_model:
                raise ValueError(f"Dataset with ID {dataset.id} not found")
            
            dataset_model.name = dataset.name
            dataset_model.description = dataset.description
            dataset_model.updated_at = datetime.now()
            dataset_model.user_id = dataset.user_id
            dataset_model.row_count = dataset.row_count
            dataset_model.column_count = dataset.column_count
            dataset_model.tags = dataset.tags
            dataset_model.is_public = dataset.is_public
            dataset_model.prompt_strategy = dataset.prompt_strategy
            
            await session.execute(delete(DatasetColumnModel).where(DatasetColumnModel.dataset_id == str(dataset.id)))
            
            for column in dataset.columns:
                column_model = DatasetColumnModel(
                    id=str(column.id),
                    dataset_id=str(dataset.id),
                    name=column.name,
                    type=column.type,
                    description=column.description
                )
                session.add(column_model)
            
            if dataset.rows:
                await session.execute(
                    delete(DatasetRowModel).where(DatasetRowModel.dataset_id == str(dataset.id))
                )
                
                for row in dataset.rows:
                    row_model = DatasetRowModel(
                        id=str(row.id),
                        dataset_id=str(dataset.id),
                        data=row.data
                    )
                    session.add(row_model)
            
            await session.commit()
            
            result_dataset = copy.deepcopy(dataset)
            result_dataset.rows = []
            return result_dataset
            
          
    
    async def delete(self, dataset_id: UUID) -> None:        
        async with self._get_session() as session:
            try:
                stmt = select(DatasetModel).where(DatasetModel.id == str(dataset_id))
                result = await session.execute(stmt)
                dataset_model = result.scalar_one_or_none()
                
                if not dataset_model:
                    raise ValueError(f"Dataset with ID {dataset_id} not found")
                
                await session.delete(dataset_model)
                await session.commit()
            except Exception as e:
                await session.rollback()
                raise
    
    async def _model_to_entity_with_relations(self, model: DatasetModel, session) -> Dataset:
        try:
            dataset = Dataset(
                name=model.name,
                description=model.description,
                user_id=model.user_id,
                id=UUID(model.id),
                created_at=model.created_at,
                updated_at=model.updated_at,
                row_count=model.row_count,
                column_count=model.column_count,
                tags=model.tags if model.tags is not None else [],
                is_public=model.is_public,
                prompt_strategy=model.prompt_strategy
            )
            
            # Always load columns since they're part of the schema definition
            columns_stmt = select(DatasetColumnModel).where(DatasetColumnModel.dataset_id == model.id)
            columns_result = await session.execute(columns_stmt)
            columns = columns_result.scalars().all()
            
            for column_model in columns:
                column = DatasetColumn(
                    name=column_model.name,
                    type=column_model.type,
                    id=UUID(column_model.id),
                    description=column_model.description
                )
                dataset.columns.append(column)
            
            # Do not load rows by default - they'll be accessed through the dedicated endpoint
            # This significantly improves performance for datasets with many rows
            
            return dataset
        except Exception as e:
            raise

    def _model_to_entity(self, model: DatasetModel) -> Dataset:
        try:
            dataset = Dataset(
                name=model.name,
                description=model.description,
                user_id=model.user_id,
                id=UUID(model.id),
                created_at=model.created_at,
                updated_at=model.updated_at,
                row_count=model.row_count,
                column_count=model.column_count,
                tags=model.tags if model.tags is not None else [],
                is_public=model.is_public,
                prompt_strategy=model.prompt_strategy
            )
            
            if hasattr(model, 'columns') and model.columns is not None:
                for column_model in model.columns:
                    column = DatasetColumn(
                        name=column_model.name,
                        type=column_model.type,
                        id=UUID(column_model.id),
                        description=column_model.description
                    )
                    dataset.columns.append(column)
                        
            if hasattr(model, 'rows') and model.rows is not None:
                for row_model in model.rows:
                    row = DatasetRow(
                        data=row_model.data,
                        id=UUID(row_model.id)
                    )
                    dataset.rows.append(row)
            
            return dataset
        except Exception as e:
            raise 