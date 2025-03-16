from typing import List, Optional, Dict, Any
from uuid import UUID
import json
from datetime import datetime

import aiomysql
from aiomysql import Pool

from ..domain.entities import Dataset, DatasetColumn, DatasetRow
from ..domain.repositories import DatasetRepository


class MySQLDatasetRepository(DatasetRepository):
    def __init__(self, pool: Pool):
        self.pool = pool

    async def save(self, dataset: Dataset) -> Dataset:
        """Save a dataset to MySQL"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # Insert dataset
                await cursor.execute(
                    """
                    INSERT INTO datasets (
                        id, name, description, created_at, updated_at, 
                        user_id, row_count, column_count, tags, is_public
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        str(dataset.id), dataset.name, dataset.description,
                        dataset.created_at.isoformat(), dataset.updated_at.isoformat(),
                        dataset.user_id, dataset.row_count, dataset.column_count,
                        json.dumps(dataset.tags), dataset.is_public
                    )
                )
                
                # Insert columns
                for column in dataset.columns:
                    await cursor.execute(
                        """
                        INSERT INTO dataset_columns (
                            id, dataset_id, name, type, description
                        ) VALUES (%s, %s, %s, %s, %s)
                        """,
                        (
                            str(column.id), str(dataset.id), column.name,
                            column.type, column.description
                        )
                    )
                
                # Insert rows
                for row in dataset.rows:
                    await cursor.execute(
                        """
                        INSERT INTO dataset_rows (
                            id, dataset_id, data
                        ) VALUES (%s, %s, %s)
                        """,
                        (
                            str(row.id), str(dataset.id), json.dumps(row.data)
                        )
                    )
                
                await conn.commit()
                
        return dataset

    async def find_by_id(self, dataset_id: UUID) -> Optional[Dataset]:
        """Find a dataset by its ID"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # Get dataset
                await cursor.execute(
                    """
                    SELECT id, name, description, created_at, updated_at, 
                           user_id, row_count, column_count, tags, is_public
                    FROM datasets
                    WHERE id = %s
                    """,
                    (str(dataset_id),)
                )
                
                dataset_row = await cursor.fetchone()
                if not dataset_row:
                    return None
                
                # Create dataset entity
                dataset = Dataset(
                    id=UUID(dataset_row[0]),
                    name=dataset_row[1],
                    description=dataset_row[2],
                    created_at=datetime.fromisoformat(dataset_row[3]),
                    updated_at=datetime.fromisoformat(dataset_row[4]),
                    user_id=dataset_row[5],
                    row_count=dataset_row[6],
                    column_count=dataset_row[7],
                    tags=json.loads(dataset_row[8]),
                    is_public=bool(dataset_row[9])
                )
                
                # Get columns
                await cursor.execute(
                    """
                    SELECT id, name, type, description
                    FROM dataset_columns
                    WHERE dataset_id = %s
                    """,
                    (str(dataset_id),)
                )
                
                columns = await cursor.fetchall()
                for column_row in columns:
                    column = DatasetColumn(
                        id=UUID(column_row[0]),
                        name=column_row[1],
                        type=column_row[2],
                        description=column_row[3]
                    )
                    dataset.columns.append(column)
                
                # Get rows
                await cursor.execute(
                    """
                    SELECT id, data
                    FROM dataset_rows
                    WHERE dataset_id = %s
                    """,
                    (str(dataset_id),)
                )
                
                rows = await cursor.fetchall()
                for row_data in rows:
                    row = DatasetRow(
                        id=UUID(row_data[0]),
                        data=json.loads(row_data[1])
                    )
                    dataset.rows.append(row)
                
        return dataset

    async def find_all(self, limit: int = 100, offset: int = 0) -> List[Dataset]:
        """Find all datasets with pagination"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    """
                    SELECT id, name, description, created_at, updated_at, 
                           user_id, row_count, column_count, tags, is_public
                    FROM datasets
                    LIMIT %s OFFSET %s
                    """,
                    (limit, offset)
                )
                
                datasets = []
                dataset_rows = await cursor.fetchall()
                
                for dataset_row in dataset_rows:
                    dataset_id = UUID(dataset_row[0])
                    
                    # Crear dataset con los datos de la consulta
                    dataset = Dataset(
                        id=dataset_id,
                        name=dataset_row[1],
                        description=dataset_row[2],
                        created_at=datetime.fromisoformat(dataset_row[3]),
                        updated_at=datetime.fromisoformat(dataset_row[4]),
                        user_id=dataset_row[5],
                        row_count=dataset_row[6],
                        column_count=dataset_row[7],
                        tags=json.loads(dataset_row[8]),
                        is_public=bool(dataset_row[9])
                    )
                    
                    # Obtener columnas
                    await cursor.execute(
                        """
                        SELECT id, name, type, description
                        FROM dataset_columns
                        WHERE dataset_id = %s
                        """,
                        (str(dataset_id),)
                    )
                    
                    column_rows = await cursor.fetchall()
                    columns = []
                    
                    for column_row in column_rows:
                        column = DatasetColumn(
                            id=UUID(column_row[0]),
                            name=column_row[1],
                            type=column_row[2],
                            description=column_row[3]
                        )
                        columns.append(column)
                    
                    dataset.columns = columns
                    datasets.append(dataset)
                
        return datasets

    async def find_by_user_id(self, user_id: str, limit: int = 100, offset: int = 0) -> List[Dataset]:
        """Find all datasets for a specific user"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    """
                    SELECT id, name, description, created_at, updated_at, 
                           user_id, row_count, column_count, tags, is_public
                    FROM datasets
                    WHERE user_id = %s
                    LIMIT %s OFFSET %s
                    """,
                    (user_id, limit, offset)
                )
                
                datasets = []
                dataset_rows = await cursor.fetchall()
                
                for dataset_row in dataset_rows:
                    dataset_id = UUID(dataset_row[0])
                    
                    # Crear dataset con los datos de la consulta
                    dataset = Dataset(
                        id=dataset_id,
                        name=dataset_row[1],
                        description=dataset_row[2],
                        created_at=datetime.fromisoformat(dataset_row[3]),
                        updated_at=datetime.fromisoformat(dataset_row[4]),
                        user_id=dataset_row[5],
                        row_count=dataset_row[6],
                        column_count=dataset_row[7],
                        tags=json.loads(dataset_row[8]),
                        is_public=bool(dataset_row[9])
                    )
                    
                    # Obtener columnas
                    await cursor.execute(
                        """
                        SELECT id, name, type, description
                        FROM dataset_columns
                        WHERE dataset_id = %s
                        """,
                        (str(dataset_id),)
                    )
                    
                    column_rows = await cursor.fetchall()
                    columns = []
                    
                    for column_row in column_rows:
                        column = DatasetColumn(
                            id=UUID(column_row[0]),
                            name=column_row[1],
                            type=column_row[2],
                            description=column_row[3]
                        )
                        columns.append(column)
                    
                    dataset.columns = columns
                    datasets.append(dataset)
                
        return datasets

    async def find_public(self, limit: int = 100, offset: int = 0) -> List[Dataset]:
        """Find all public datasets"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    """
                    SELECT id, name, description, created_at, updated_at, 
                           user_id, row_count, column_count, tags, is_public
                    FROM datasets
                    WHERE is_public = TRUE
                    LIMIT %s OFFSET %s
                    """,
                    (limit, offset)
                )
                
                datasets = []
                dataset_rows = await cursor.fetchall()
                
                for dataset_row in dataset_rows:
                    dataset_id = UUID(dataset_row[0])
                    
                    # Crear dataset con los datos de la consulta
                    dataset = Dataset(
                        id=dataset_id,
                        name=dataset_row[1],
                        description=dataset_row[2],
                        created_at=datetime.fromisoformat(dataset_row[3]),
                        updated_at=datetime.fromisoformat(dataset_row[4]),
                        user_id=dataset_row[5],
                        row_count=dataset_row[6],
                        column_count=dataset_row[7],
                        tags=json.loads(dataset_row[8]),
                        is_public=bool(dataset_row[9])
                    )
                    
                    # Obtener columnas
                    await cursor.execute(
                        """
                        SELECT id, name, type, description
                        FROM dataset_columns
                        WHERE dataset_id = %s
                        """,
                        (str(dataset_id),)
                    )
                    
                    column_rows = await cursor.fetchall()
                    columns = []
                    
                    for column_row in column_rows:
                        column = DatasetColumn(
                            id=UUID(column_row[0]),
                            name=column_row[1],
                            type=column_row[2],
                            description=column_row[3]
                        )
                        columns.append(column)
                    
                    dataset.columns = columns
                    datasets.append(dataset)
                
        return datasets

    async def delete(self, dataset_id: UUID) -> bool:
        """Delete a dataset by its ID"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # Delete rows
                await cursor.execute(
                    "DELETE FROM dataset_rows WHERE dataset_id = %s",
                    (str(dataset_id),)
                )
                
                # Delete columns
                await cursor.execute(
                    "DELETE FROM dataset_columns WHERE dataset_id = %s",
                    (str(dataset_id),)
                )
                
                # Delete dataset
                await cursor.execute(
                    "DELETE FROM datasets WHERE id = %s",
                    (str(dataset_id),)
                )
                
                await conn.commit()
                
                return cursor.rowcount > 0

    async def update(self, dataset: Dataset) -> Dataset:
        """Update an existing dataset"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # Update dataset
                await cursor.execute(
                    """
                    UPDATE datasets
                    SET name = %s, description = %s, updated_at = %s,
                        row_count = %s, column_count = %s, tags = %s, is_public = %s
                    WHERE id = %s
                    """,
                    (
                        dataset.name, dataset.description, dataset.updated_at.isoformat(),
                        dataset.row_count, dataset.column_count, json.dumps(dataset.tags),
                        dataset.is_public, str(dataset.id)
                    )
                )
                
                # Delete existing columns and rows to replace them
                await cursor.execute(
                    "DELETE FROM dataset_columns WHERE dataset_id = %s",
                    (str(dataset.id),)
                )
                
                await cursor.execute(
                    "DELETE FROM dataset_rows WHERE dataset_id = %s",
                    (str(dataset.id),)
                )
                
                # Insert updated columns
                for column in dataset.columns:
                    await cursor.execute(
                        """
                        INSERT INTO dataset_columns (
                            id, dataset_id, name, type, description
                        ) VALUES (%s, %s, %s, %s, %s)
                        """,
                        (
                            str(column.id), str(dataset.id), column.name,
                            column.type, column.description
                        )
                    )
                
                # Insert updated rows
                for row in dataset.rows:
                    await cursor.execute(
                        """
                        INSERT INTO dataset_rows (
                            id, dataset_id, data
                        ) VALUES (%s, %s, %s)
                        """,
                        (
                            str(row.id), str(dataset.id), json.dumps(row.data)
                        )
                    )
                
                await conn.commit()
                
        return dataset 