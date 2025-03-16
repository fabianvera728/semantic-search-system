from typing import Dict, List, Optional
from uuid import UUID
import copy

from ..domain.entities import Dataset
from ..domain.repositories import DatasetRepository


class InMemoryDatasetRepository(DatasetRepository):
    def __init__(self):
        self.datasets: Dict[str, Dataset] = {}

    async def save(self, dataset: Dataset) -> Dataset:
        """Save a dataset to the in-memory store"""
        # Store a deep copy to prevent reference issues
        self.datasets[str(dataset.id)] = copy.deepcopy(dataset)
        return dataset

    async def find_by_id(self, dataset_id: UUID) -> Optional[Dataset]:
        """Find a dataset by its ID"""
        dataset = self.datasets.get(str(dataset_id))
        if dataset:
            return copy.deepcopy(dataset)
        return None

    async def find_all(self, limit: int = 100, offset: int = 0) -> List[Dataset]:
        """Find all datasets with pagination"""
        all_datasets = list(self.datasets.values())
        paginated = all_datasets[offset:offset + limit]
        return [copy.deepcopy(dataset) for dataset in paginated]

    async def find_by_user_id(self, user_id: str, limit: int = 100, offset: int = 0) -> List[Dataset]:
        """Find all datasets for a specific user"""
        user_datasets = [
            dataset for dataset in self.datasets.values()
            if dataset.user_id == user_id
        ]
        paginated = user_datasets[offset:offset + limit]
        return [copy.deepcopy(dataset) for dataset in paginated]

    async def find_public(self, limit: int = 100, offset: int = 0) -> List[Dataset]:
        """Find all public datasets"""
        public_datasets = [
            dataset for dataset in self.datasets.values()
            if dataset.is_public
        ]
        paginated = public_datasets[offset:offset + limit]
        return [copy.deepcopy(dataset) for dataset in paginated]

    async def delete(self, dataset_id: UUID) -> bool:
        """Delete a dataset by its ID"""
        if str(dataset_id) in self.datasets:
            del self.datasets[str(dataset_id)]
            return True
        return False

    async def update(self, dataset: Dataset) -> Dataset:
        """Update an existing dataset"""
        if str(dataset.id) not in self.datasets:
            return None
        
        # Store a deep copy to prevent reference issues
        self.datasets[str(dataset.id)] = copy.deepcopy(dataset)
        return dataset 