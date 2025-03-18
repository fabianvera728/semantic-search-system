import logging
import uuid
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime
from uuid import UUID
import chromadb
from chromadb.utils import embedding_functions

from src.config import AppConfig
from src.contexts.embedding.domain import (
    EmbeddingRepository,
    DatasetRepository,
    Embedding,
    EmbeddingBatch,
    Dataset,
    EmbeddingModel,
    GenerateEmbeddingRequest,
    BatchEmbeddingRequest,
    ListEmbeddingsRequest,
    GetEmbeddingRequest,
    DeleteEmbeddingRequest,
    CreateDatasetRequest,
    EmbeddingNotFoundError,
    DatasetNotFoundError,
    VectorDBError
)
from sentence_transformers import SentenceTransformer
from src.infrastructure.db import get_chromadb_client, get_or_create_collection

logger = logging.getLogger(__name__)


class ChromaEmbeddingRepository(EmbeddingRepository):
    def __init__(self, config: AppConfig):
        self.config = config
        self.model_name = config.embedding_model
        self.model = None
        self._initialize_model()
    
    def _initialize_model(self):
        try:
            # Load the model
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"Loaded embedding model: {self.model_name}")
        except Exception as e:
            logger.error(f"Error loading embedding model {self.model_name}: {str(e)}")
            raise
    
    async def get_chroma_client(self):
        return await get_chromadb_client()
    
    def _get_dataset_collection_name(self, dataset_id: str) -> str:
        """Get the ChromaDB collection name for a dataset."""
        return f"dataset_{dataset_id}"
    
    async def generate_embedding(self, request: GenerateEmbeddingRequest) -> Embedding:
        """Generate a single embedding."""
        try:
            # Generate embedding
            vector = self.model.encode([request.text])[0]
            
            # Create embedding entity
            embedding = Embedding(
                id=uuid.uuid4() if request.batch_id is None else uuid.uuid4(),
                vector=vector,
                text=request.text,
                dataset_id=request.dataset_id,
                row_id=request.row_id,
                metadata=request.metadata,
                created_at=datetime.now()
            )
            
            return embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise
    
    async def generate_batch_embeddings(self, request: BatchEmbeddingRequest) -> EmbeddingBatch:
        """Generate embeddings for a batch of texts."""
        try:
            # Generate embeddings
            vectors = self.model.encode(request.texts)
            
            # Create embedding batch
            batch = EmbeddingBatch(
                dataset_id=request.dataset_id,
                metadata=request.metadata
            )
            
            # Create individual embeddings
            for i, text in enumerate(request.texts):
                embedding = Embedding(
                    id=uuid.uuid4(),
                    vector=vectors[i],
                    text=text,
                    dataset_id=request.dataset_id,
                    row_id=request.row_ids[i],
                    metadata=request.metadata,
                    created_at=datetime.now()
                )
                batch.add_embedding(embedding)
            
            return batch
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {str(e)}")
            raise
    
    async def save_embedding(self, embedding: Embedding) -> Embedding:
        """Save a single embedding to ChromaDB."""
        try:
            # Get ChromaDB client
            client = await self.get_chroma_client()
            
            # Get or create collection for dataset
            collection_name = self._get_dataset_collection_name(embedding.dataset_id)
            collection = get_or_create_collection(client, collection_name)
            
            # Add embedding to ChromaDB
            collection.add(
                ids=[str(embedding.id)],
                embeddings=[embedding.vector.tolist()],
                metadatas=[{
                    "dataset_id": embedding.dataset_id,
                    "row_id": embedding.row_id,
                    "model_name": self.model_name,
                    "created_at": embedding.created_at.isoformat(),
                    **embedding.metadata
                }],
                documents=[embedding.text]
            )
            
            return embedding
        except Exception as e:
            logger.error(f"Error saving embedding: {str(e)}")
            raise VectorDBError(f"Failed to save embedding: {str(e)}", "chromadb", e)
    
    async def save_batch_embeddings(self, batch: EmbeddingBatch) -> EmbeddingBatch:
        """Save a batch of embeddings to ChromaDB."""
        if not batch.embeddings:
            return batch
        
        try:
            # Get ChromaDB client
            client = await self.get_chroma_client()
            
            # Get or create collection for dataset
            collection_name = self._get_dataset_collection_name(batch.dataset_id)
            collection = get_or_create_collection(client, collection_name)
            
            # Prepare data for batch import
            ids = [str(embedding.id) for embedding in batch.embeddings]
            embeddings = [embedding.vector.tolist() for embedding in batch.embeddings]
            metadatas = [{
                "dataset_id": embedding.dataset_id,
                "row_id": embedding.row_id,
                "model_name": self.model_name,
                "created_at": embedding.created_at.isoformat(),
                **embedding.metadata
            } for embedding in batch.embeddings]
            documents = [embedding.text for embedding in batch.embeddings]
            
            # Add embeddings to ChromaDB
            collection.add(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=documents
            )
            
            return batch
        except Exception as e:
            logger.error(f"Error saving batch embeddings: {str(e)}")
            raise VectorDBError(f"Failed to save batch embeddings: {str(e)}", "chromadb", e)
    
    async def get_embedding(self, request: GetEmbeddingRequest) -> Optional[Embedding]:
        """Get a single embedding from ChromaDB."""
        try:
            # Get ChromaDB client
            client = await self.get_chroma_client()
            
            # Check if collection exists
            collections = client.list_collections()
            collection_name = self._get_dataset_collection_name(request.dataset_id)
            
            if not any(c.name == collection_name for c in collections):
                raise DatasetNotFoundError(request.dataset_id)
            
            # Get collection
            collection = client.get_collection(collection_name)
            
            # Get embedding
            result = collection.get(
                ids=[str(request.embedding_id)],
                include=["embeddings", "documents", "metadatas"]
            )
            
            if not result["ids"]:
                return None
            
            # Create embedding entity
            metadata = result["metadatas"][0] if result["metadatas"] else {}
            vector = np.array(result["embeddings"][0]) if result["embeddings"] else None
            text = result["documents"][0] if result["documents"] else ""
            
            embedding = Embedding(
                id=UUID(result["ids"][0]),
                vector=vector,
                text=text,
                dataset_id=request.dataset_id,
                row_id=metadata.get("row_id", ""),
                metadata={k: v for k, v in metadata.items() if k not in ["dataset_id", "row_id", "model_name", "created_at"]},
                created_at=datetime.fromisoformat(metadata.get("created_at", datetime.now().isoformat()))
            )
            
            return embedding
        except DatasetNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error getting embedding: {str(e)}")
            raise VectorDBError(f"Failed to get embedding: {str(e)}", "chromadb", e)
    
    async def list_embeddings(self, request: ListEmbeddingsRequest) -> List[Embedding]:
        """List embeddings from ChromaDB with pagination."""
        try:
            # Get ChromaDB client
            client = await self.get_chroma_client()
            
            # Check if collection exists
            collections = client.list_collections()
            collection_name = self._get_dataset_collection_name(request.dataset_id)
            
            if not any(c.name == collection_name for c in collections):
                raise DatasetNotFoundError(request.dataset_id)
            
            # Get collection
            collection = client.get_collection(collection_name)
            
            # Build query filters
            where = {"dataset_id": request.dataset_id}
            if request.filter_criteria:
                for key, value in request.filter_criteria.items():
                    where[key] = value
            
            # Get embeddings (ChromaDB doesn't support direct pagination, retrieve all and paginate in memory)
            result = collection.get(
                include=["embeddings", "documents", "metadatas"],
                where=where
            )
            
            # Paginate results
            start = request.offset
            end = start + request.limit
            paginated_ids = result["ids"][start:end] if result["ids"] else []
            
            if not paginated_ids:
                return []
            
            # Get paginated data
            paginated_result = collection.get(
                ids=paginated_ids,
                include=["embeddings", "documents", "metadatas"]
            )
            
            # Create embedding entities
            embeddings = []
            for i, embedding_id in enumerate(paginated_result["ids"]):
                metadata = paginated_result["metadatas"][i] if paginated_result["metadatas"] else {}
                vector = np.array(paginated_result["embeddings"][i]) if paginated_result["embeddings"] else None
                text = paginated_result["documents"][i] if paginated_result["documents"] else ""
                
                embedding = Embedding(
                    id=UUID(embedding_id),
                    vector=vector,
                    text=text,
                    dataset_id=request.dataset_id,
                    row_id=metadata.get("row_id", ""),
                    metadata={k: v for k, v in metadata.items() if k not in ["dataset_id", "row_id", "model_name", "created_at"]},
                    created_at=datetime.fromisoformat(metadata.get("created_at", datetime.now().isoformat()))
                )
                
                embeddings.append(embedding)
            
            return embeddings
        except DatasetNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error listing embeddings: {str(e)}")
            raise VectorDBError(f"Failed to list embeddings: {str(e)}", "chromadb", e)
    
    async def delete_embedding(self, request: DeleteEmbeddingRequest) -> bool:
        """Delete a single embedding from ChromaDB."""
        try:
            # Get ChromaDB client
            client = await self.get_chroma_client()
            
            # Check if collection exists
            collections = client.list_collections()
            collection_name = self._get_dataset_collection_name(request.dataset_id)
            
            if not any(c.name == collection_name for c in collections):
                raise DatasetNotFoundError(request.dataset_id)
            
            # Get collection
            collection = client.get_collection(collection_name)
            
            # Delete embedding
            collection.delete(ids=[str(request.embedding_id)])
            
            return True
        except DatasetNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error deleting embedding: {str(e)}")
            raise VectorDBError(f"Failed to delete embedding: {str(e)}", "chromadb", e)
    
    async def delete_dataset_embeddings(self, dataset_id: str) -> int:
        """Delete all embeddings for a dataset."""
        try:
            # Get ChromaDB client
            client = await self.get_chroma_client()
            
            # Check if collection exists
            collections = client.list_collections()
            collection_name = self._get_dataset_collection_name(dataset_id)
            
            if not any(c.name == collection_name for c in collections):
                return 0
            
            # Get collection
            collection = client.get_collection(collection_name)
            
            # Get count before deletion
            count = collection.count()
            
            # Delete all embeddings in collection
            collection.delete()
            
            return count
        except Exception as e:
            logger.error(f"Error deleting dataset embeddings: {str(e)}")
            raise VectorDBError(f"Failed to delete dataset embeddings: {str(e)}", "chromadb", e)
    
    async def get_models(self) -> List[EmbeddingModel]:
        """Get all available embedding models."""
        # For now, return just the configured model
        return [
            EmbeddingModel(
                name=self.model_name,
                dimension=self.model.get_sentence_embedding_dimension(),
                metadata={"type": "sentence-transformers"}
            )
        ]
    
    async def get_model(self, model_name: str) -> Optional[EmbeddingModel]:
        """Get specific embedding model information."""
        if model_name == self.model_name:
            return EmbeddingModel(
                name=self.model_name,
                dimension=self.model.get_sentence_embedding_dimension(),
                metadata={"type": "sentence-transformers"}
            )
        
        # Could be extended to support more models
        return None


class ChromaDatasetRepository(DatasetRepository):
    def __init__(self, config: AppConfig):
        self.config = config
    
    async def get_chroma_client(self):
        return await get_chromadb_client()
    
    def _get_dataset_collection_name(self, dataset_id: str) -> str:
        """Get the ChromaDB collection name for a dataset."""
        return f"dataset_{dataset_id}"
    
    def _get_datasets_collection_name(self) -> str:
        """Get the ChromaDB collection name for datasets metadata."""
        return "datasets_metadata"
    
    async def create_dataset(self, request: CreateDatasetRequest) -> Dataset:
        """Create a new dataset in ChromaDB."""
        try:
            # Get ChromaDB client
            client = await self.get_chroma_client()
            
            # Create collection for dataset
            collection_name = self._get_dataset_collection_name(request.dataset_id)
            collection = get_or_create_collection(client, collection_name, {
                "name": request.name,
                "dimension": request.dimension,
                "created_at": datetime.now().isoformat()
            })
            
            # Get datasets metadata collection
            metadata_collection = get_or_create_collection(client, self._get_datasets_collection_name())
            
            # Create dataset entity
            dataset = Dataset(
                id=request.dataset_id,
                name=request.name,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                embedding_count=0
            )
            
            # Save dataset metadata
            metadata_collection.add(
                ids=[dataset.id],
                embeddings=[[0] * 8],  # Dummy embedding
                metadatas=[{
                    "name": dataset.name,
                    "dimension": request.dimension,
                    "embedding_count": 0,
                    "created_at": dataset.created_at.isoformat(),
                    "updated_at": dataset.updated_at.isoformat()
                }],
                documents=[f"Dataset: {dataset.name}"]
            )
            
            return dataset
        except Exception as e:
            logger.error(f"Error creating dataset: {str(e)}")
            raise VectorDBError(f"Failed to create dataset: {str(e)}", "chromadb", e)
    
    async def get_dataset(self, dataset_id: str) -> Optional[Dataset]:
        """Get dataset information from ChromaDB."""
        try:
            # Get ChromaDB client
            client = await self.get_chroma_client()
            
            # Get datasets metadata collection
            try:
                metadata_collection = client.get_collection(self._get_datasets_collection_name())
            except ValueError:
                # Collection doesn't exist
                return None
            
            # Get dataset metadata
            result = metadata_collection.get(
                ids=[dataset_id],
                include=["metadatas"]
            )
            
            if not result["ids"]:
                return None
            
            # Create dataset entity
            metadata = result["metadatas"][0]
            
            dataset = Dataset(
                id=dataset_id,
                name=metadata.get("name", f"Dataset {dataset_id}"),
                created_at=datetime.fromisoformat(metadata.get("created_at", datetime.now().isoformat())),
                updated_at=datetime.fromisoformat(metadata.get("updated_at", datetime.now().isoformat())),
                embedding_count=metadata.get("embedding_count", 0)
            )
            
            return dataset
        except Exception as e:
            logger.error(f"Error getting dataset: {str(e)}")
            raise VectorDBError(f"Failed to get dataset: {str(e)}", "chromadb", e)
    
    async def delete_dataset(self, dataset_id: str) -> bool:
        """Delete a dataset from ChromaDB."""
        try:
            # Get ChromaDB client
            client = await self.get_chroma_client()
            
            # Delete dataset collection
            collection_name = self._get_dataset_collection_name(dataset_id)
            try:
                client.delete_collection(collection_name)
            except ValueError:
                # Collection doesn't exist
                pass
            
            # Delete dataset metadata
            try:
                metadata_collection = client.get_collection(self._get_datasets_collection_name())
                metadata_collection.delete(ids=[dataset_id])
            except ValueError:
                # Metadata collection doesn't exist
                pass
            
            return True
        except Exception as e:
            logger.error(f"Error deleting dataset: {str(e)}")
            raise VectorDBError(f"Failed to delete dataset: {str(e)}", "chromadb", e)
    
    async def list_datasets(self, limit: int = 100, offset: int = 0) -> List[Dataset]:
        """List datasets with pagination."""
        try:
            # Get ChromaDB client
            client = await self.get_chroma_client()
            
            # Get datasets metadata collection
            try:
                metadata_collection = client.get_collection(self._get_datasets_collection_name())
            except ValueError:
                # Collection doesn't exist
                return []
            
            # Get all datasets (ChromaDB doesn't support direct pagination)
            result = metadata_collection.get(
                include=["metadatas"]
            )
            
            # Paginate results
            paginated_ids = result["ids"][offset:offset+limit] if result["ids"] else []
            
            if not paginated_ids:
                return []
            
            # Get paginated metadata
            paginated_result = metadata_collection.get(
                ids=paginated_ids,
                include=["metadatas"]
            )
            
            # Create dataset entities
            datasets = []
            for i, dataset_id in enumerate(paginated_result["ids"]):
                metadata = paginated_result["metadatas"][i]
                
                dataset = Dataset(
                    id=dataset_id,
                    name=metadata.get("name", f"Dataset {dataset_id}"),
                    created_at=datetime.fromisoformat(metadata.get("created_at", datetime.now().isoformat())),
                    updated_at=datetime.fromisoformat(metadata.get("updated_at", datetime.now().isoformat())),
                    embedding_count=metadata.get("embedding_count", 0)
                )
                
                datasets.append(dataset)
            
            return datasets
        except Exception as e:
            logger.error(f"Error listing datasets: {str(e)}")
            raise VectorDBError(f"Failed to list datasets: {str(e)}", "chromadb", e)
    
    async def update_dataset(self, dataset: Dataset) -> Dataset:
        """Update dataset information."""
        try:
            # Get ChromaDB client
            client = await self.get_chroma_client()
            
            # Get datasets metadata collection
            try:
                metadata_collection = client.get_collection(self._get_datasets_collection_name())
            except ValueError:
                # Create metadata collection
                metadata_collection = client.create_collection(self._get_datasets_collection_name())
            
            # Update dataset metadata
            metadata_collection.update(
                ids=[dataset.id],
                metadatas=[{
                    "name": dataset.name,
                    "embedding_count": dataset.embedding_count,
                    "updated_at": datetime.now().isoformat()
                }]
            )
            
            # Set updated_at
            dataset.updated_at = datetime.now()
            
            return dataset
        except Exception as e:
            logger.error(f"Error updating dataset: {str(e)}")
            raise VectorDBError(f"Failed to update dataset: {str(e)}", "chromadb", e) 