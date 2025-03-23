from src.contexts.embedding.domain import DatasetRepository, CreateDatasetRequest, Dataset, VectorDBError
from src.infrastructure.db import get_chromadb_client
from src.config import AppConfig
from datetime import datetime
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

class ChromaDatasetRepository(DatasetRepository):
    def __init__(self, config: AppConfig):
        self.config = config
    
    async def get_chroma_client(self):
        return await get_chromadb_client()
    
    def _get_dataset_collection_name(self, dataset_id: str) -> str:
        return f"dataset_{dataset_id}"
    
    def _get_datasets_collection_name(self) -> str:
        return "datasets_metadata"
    
    async def _get_or_create_collection(self, client, collection_name, metadata):
        try:
            logger.info(f"Creating collection: {collection_name}")
            collection = client.create_collection(
                name=collection_name,
                metadata=metadata
            )
            logger.info(f"Collection created successfully: {collection_name}")
            return collection
        except Exception as e:
            if "already exists" in str(e):
                logger.info(f"Collection {collection_name} already exists, retrieving it")
                return client.get_collection(name=collection_name)
            raise e
            
    async def _prepare_dataset_metadata(self, request):
        metadata = {
            "name": request.name,
            "dimension": request.dimension,
            "dataset_id": request.dataset_id,
            "created_at": datetime.now().isoformat()
        }
        
        if request.metadata and isinstance(request.metadata, dict) and len(request.metadata) > 0:
            metadata.update(request.metadata)
        else:
            metadata["custom_data"] = "true"
            
        return metadata
        
    async def _save_dataset_metadata(self, client, dataset, dimension):
        metadata_collection_name = self._get_datasets_collection_name()
        metadata_collection_metadata = {
            "type": "datasets_metadata", 
            "created_at": datetime.now().isoformat()
        }
        
        metadata_collection = await self._get_or_create_collection(
            client, 
            metadata_collection_name,
            metadata_collection_metadata
        )
        
        save_metadata = {
            "name": dataset.name,
            "dataset_id": str(dataset.id),
            "dimension": dimension,
            "embedding_count": 0,
            "created_at": dataset.created_at.isoformat(),
            "updated_at": dataset.updated_at.isoformat()
        }

        try:
            metadata_collection.add(
                ids=[str(dataset.id)],
                embeddings=[[0] * 8],
                metadatas=[save_metadata],
                documents=[f"Dataset: {dataset.name}"]
            )
            logger.info(f"Added dataset metadata with ID: {dataset.id}")
        except Exception as add_error:
            logger.error(f"Error adding dataset metadata: {str(add_error)}")
    
    async def create_dataset(self, request: CreateDatasetRequest) -> Dataset:
        try:
            client = await self.get_chroma_client()
            
            collection_metadata = await self._prepare_dataset_metadata(request)
            collection_name = self._get_dataset_collection_name(request.dataset_id)
            
            await self._get_or_create_collection(client, collection_name, collection_metadata)
            
            dataset = Dataset(
                id=request.dataset_id,
                name=request.name,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                embedding_count=0,
                metadata=collection_metadata
            )
            
            await self._save_dataset_metadata(client, dataset, request.dimension)
            
            return dataset
        except Exception as e:
            logger.error(f"Error creating dataset: {str(e)}")
            raise VectorDBError(f"Failed to create dataset: {str(e)}", "chromadb", e)
    
    async def _get_collection_metadata(self, client, collection_name):
        try:
            logger.debug(f"Checking if collection exists: {collection_name}")
            collection = client.get_collection(collection_name)
            if hasattr(collection, 'metadata') and collection.metadata:
                logger.debug(f"Found collection metadata: {collection.metadata}")
                return collection.metadata, True
            return {}, True
        except Exception as e:
            logger.debug(f"Collection {collection_name} not found: {str(e)}")
            return {}, False
            
    async def _get_metadata_from_metadata_collection(self, client, dataset_id):
        try:
            metadata_collection = client.get_collection(self._get_datasets_collection_name())
            result = metadata_collection.get(
                ids=[dataset_id],
                include=["metadatas"]
            )
            
            if result["ids"]:
                metadata = result["metadatas"][0]
                logger.debug(f"Found dataset metadata: {metadata}")
                return metadata
        except Exception as e:
            logger.debug(f"Error getting dataset metadata: {str(e)}")
        
        return None
        
    def _parse_datetime(self, datetime_str):
        try:
            return datetime.fromisoformat(datetime_str)
        except:
            return datetime.now()
            
    async def get_dataset(self, dataset_id: str) -> Optional[Dataset]:
        try:
            dataset_id_str = str(dataset_id)            
            client = await self.get_chroma_client()            
            collection_name = self._get_dataset_collection_name(dataset_id_str)
            collection_metadata, collection_exists = await self._get_collection_metadata(client, collection_name)            
            metadata_from_collection = await self._get_metadata_from_metadata_collection(client, dataset_id_str)
            
            if not collection_exists and not metadata_from_collection:
                logger.info(f"Dataset {dataset_id} not found")
                return None
            
            name = collection_metadata.get("name", f"Dataset {dataset_id}")
            created_at_str = collection_metadata.get("created_at", datetime.now().isoformat())
            updated_at_str = collection_metadata.get("updated_at", datetime.now().isoformat())
            embedding_count = 0
            
            if metadata_from_collection:
                name = metadata_from_collection.get("name", name)
                created_at_str = metadata_from_collection.get("created_at", created_at_str)
                updated_at_str = metadata_from_collection.get("updated_at", updated_at_str)
                embedding_count = metadata_from_collection.get("embedding_count", embedding_count)
            
            dataset = Dataset(
                id=dataset_id_str,
                name=name,
                created_at=self._parse_datetime(created_at_str),
                updated_at=self._parse_datetime(updated_at_str),
                embedding_count=embedding_count,
                metadata=collection_metadata
            )
            
            return dataset
                
        except Exception as e:
            raise VectorDBError(f"Failed to get dataset: {str(e)}", "chromadb", e)
    
    async def delete_dataset(self, dataset_id: str) -> bool:
        try:
            client = await self.get_chroma_client()
            
            collection_name = self._get_dataset_collection_name(dataset_id)
            try:
                client.delete_collection(collection_name)
            except ValueError:
                pass
            
            try:
                metadata_collection = client.get_collection(self._get_datasets_collection_name())
                metadata_collection.delete(ids=[dataset_id])
            except ValueError:
                pass
            
            return True
        except Exception as e:
            logger.error(f"Error deleting dataset: {str(e)}")
            raise VectorDBError(f"Failed to delete dataset: {str(e)}", "chromadb", e)
    
    async def list_datasets(self, limit: int = 100, offset: int = 0) -> List[Dataset]:
        try:
            client = await self.get_chroma_client()
            
            try:
                metadata_collection = client.get_collection(self._get_datasets_collection_name())
            except ValueError:
                return []
            
            result = metadata_collection.get(
                include=["metadatas"]
            )
            
            paginated_ids = result["ids"][offset:offset+limit] if result["ids"] else []
            
            if not paginated_ids:
                return []
            
            paginated_result = metadata_collection.get(
                ids=paginated_ids,
                include=["metadatas"]
            )
            
            datasets = []
            for i, dataset_id in enumerate(paginated_result["ids"]):
                metadata = paginated_result["metadatas"][i]
                
                collection_metadata = {}
                try:
                    collection_name = self._get_dataset_collection_name(dataset_id)
                    collection = client.get_collection(collection_name)
                    if hasattr(collection, 'metadata') and collection.metadata:
                        collection_metadata = collection.metadata
                except ValueError:
                    pass
                
                dataset = Dataset(
                    id=dataset_id,
                    name=metadata.get("name", f"Dataset {dataset_id}"),
                    created_at=datetime.fromisoformat(metadata.get("created_at", datetime.now().isoformat())),
                    updated_at=datetime.fromisoformat(metadata.get("updated_at", datetime.now().isoformat())),
                    embedding_count=metadata.get("embedding_count", 0),
                    metadata=collection_metadata
                )
                
                datasets.append(dataset)
            
            return datasets
        except Exception as e:
            logger.error(f"Error listing datasets: {str(e)}")
            raise VectorDBError(f"Failed to list datasets: {str(e)}", "chromadb", e)
    
    async def update_dataset(self, dataset: Dataset) -> Dataset:
        try:
            client = await self.get_chroma_client()
            
            try:
                metadata_collection = client.get_collection(self._get_datasets_collection_name())
            except ValueError:
                metadata_collection = client.create_collection(self._get_datasets_collection_name())
            
            metadata_collection.update(
                ids=[dataset.id],
                metadatas=[{
                    "name": dataset.name,
                    "embedding_count": dataset.embedding_count,
                    "updated_at": datetime.now().isoformat()
                }]
            )
            
            dataset.updated_at = datetime.now()
            
            return dataset
        except Exception as e:
            logger.error(f"Error updating dataset: {str(e)}")
            raise VectorDBError(f"Failed to update dataset: {str(e)}", "chromadb", e) 