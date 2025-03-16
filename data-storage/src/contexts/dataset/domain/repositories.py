from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from .entities import Dataset


class DatasetRepository(ABC):
    @abstractmethod
    async def save(self, dataset: Dataset) -> Dataset:
        """Save a dataset to the repository"""
        pass

    @abstractmethod
    async def find_by_id(self, dataset_id: UUID) -> Optional[Dataset]:
        """Find a dataset by its ID"""
        pass

    @abstractmethod
    async def find_all(self, limit: int = 100, offset: int = 0) -> List[Dataset]:
        """Find all datasets with pagination"""
        pass

    @abstractmethod
    async def find_by_user_id(self, user_id: str, limit: int = 100, offset: int = 0) -> List[Dataset]:
        """Find all datasets for a specific user"""
        pass

    @abstractmethod
    async def find_public(self, limit: int = 100, offset: int = 0) -> List[Dataset]:
        """Find all public datasets"""
        pass

    @abstractmethod
    async def delete(self, dataset_id: UUID) -> bool:
        """Delete a dataset by its ID"""
        pass

    @abstractmethod
    async def update(self, dataset: Dataset) -> Dataset:
        """Update an existing dataset"""
        pass 