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
        logger.info(f"Guardando dataset: {dataset.name} (ID: {dataset.id})")
        
        async with self._get_session() as session:
            logger.info(f"Sesión obtenida: {session} 🚀🚀🚀🚀🚀🚀")
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
                    is_public=dataset.is_public
                )
                
                session.add(dataset_model)
                await session.flush()
                
                # Agregar columnas
                for column in dataset.columns:
                    column_model = DatasetColumnModel(
                        id=str(column.id),
                        dataset_id=str(dataset.id),
                        name=column.name,
                        type=column.type,
                        description=column.description
                    )
                    session.add(column_model)
                
                for row in dataset.rows:
                    row_model = DatasetRowModel(
                        id=str(row.id),
                        dataset_id=str(dataset.id),
                        data=row.data
                    )
                    session.add(row_model)
                
                await session.commit()
                logger.info(f"Dataset guardado exitosamente: {dataset.name} (ID: {dataset.id})")
                
                return copy.deepcopy(dataset)
            except Exception as e:
                await session.rollback()
                logger.error(f"Error al guardar dataset: {e}")
                raise
    
    async def find_by_id(self, dataset_id: str) -> Optional[Dataset]:
        async with self._get_session() as session:
            stmt = select(DatasetModel).where(DatasetModel.id == dataset_id)
            result = await session.execute(stmt)
            dataset_model = result.scalar_one_or_none()
            
            if not dataset_model:
                return None
            
            return self._model_to_entity(dataset_model)
    
    async def find_by_user_id(self, user_id: str, skip: int = 0, limit: int = 100) -> List[Dataset]:
        async with self._get_session() as session:
            stmt = select(DatasetModel).where(DatasetModel.user_id == user_id).offset(skip).limit(limit)
            result = await session.execute(stmt)
            dataset_models = result.scalars().all()
            
            return [self._model_to_entity(model) for model in dataset_models]
    
    async def find_public(self, skip: int = 0, limit: int = 100) -> List[Dataset]:
        async with self._get_session() as session:
            stmt = select(DatasetModel).where(DatasetModel.is_public == True).offset(skip).limit(limit)
            result = await session.execute(stmt)
            dataset_models = result.scalars().all()
            
            return [self._model_to_entity(model) for model in dataset_models]
    
    async def find_all(self, skip: int = 0, limit: int = 100) -> List[Dataset]:
        async with self._get_session() as session:
            stmt = select(DatasetModel).offset(skip).limit(limit)
            result = await session.execute(stmt)
            dataset_models = result.scalars().all()
            
            return [self._model_to_entity(model) for model in dataset_models]
    
    async def update(self, dataset: Dataset) -> Dataset:
        logger.info(f"Actualizando dataset: {dataset.name} (ID: {dataset.id})")
        
        async with self._get_session() as session:
            try:
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
                logger.info(f"Dataset actualizado exitosamente: {dataset.name} (ID: {dataset.id})")
                
                return copy.deepcopy(dataset)
            except Exception as e:
                await session.rollback()
                logger.error(f"Error al actualizar dataset: {e}")
                raise
    
    async def delete(self, dataset_id: str) -> None:
        logger.info(f"Eliminando dataset con ID: {dataset_id}")
        
        async with self._get_session() as session:
            try:
                stmt = select(DatasetModel).where(DatasetModel.id == dataset_id)
                result = await session.execute(stmt)
                dataset_model = result.scalar_one_or_none()
                
                if not dataset_model:
                    raise ValueError(f"Dataset with ID {dataset_id} not found")
                
                await session.delete(dataset_model)
                await session.commit()
                logger.info(f"Dataset eliminado exitosamente: {dataset_id}")
            except Exception as e:
                await session.rollback()
                logger.error(f"Error al eliminar dataset: {e}")
                raise
    
    def _model_to_entity(self, model: DatasetModel) -> Dataset:
        dataset = Dataset(
            name=model.name,
            description=model.description,
            user_id=model.user_id,
            id=UUID(model.id),
            created_at=model.created_at,
            updated_at=model.updated_at,
            row_count=model.row_count,
            column_count=model.column_count,
            tags=model.tags,
            is_public=model.is_public
        )
        
        for column_model in model.columns:
            column = DatasetColumn(
                name=column_model.name,
                type=column_model.type,
                id=UUID(column_model.id),
                description=column_model.description
            )
            dataset.columns.append(column)
        
        for row_model in model.rows:
            row = DatasetRow(
                data=row_model.data,
                id=UUID(row_model.id)
            )
            dataset.rows.append(row)
        
        return dataset 