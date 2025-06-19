import logging
import uuid
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime
from uuid import UUID
from src.config import AppConfig
from src.contexts.embedding.domain import (
    EmbeddingRepository,
    Embedding,
    EmbeddingBatch,
    EmbeddingModel,
    GenerateEmbeddingRequest,
    BatchEmbeddingRequest,
    ListEmbeddingsRequest,
    GetEmbeddingRequest,
    DeleteEmbeddingRequest,
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
        except Exception as e:
            raise
    
    async def get_chroma_client(self):
        return await get_chromadb_client()
    
    def _get_dataset_collection_name(self, dataset_id: str) -> str:
        return f"dataset_{dataset_id}"
    
    async def generate_embedding(self, request: GenerateEmbeddingRequest) -> Embedding:
        try:
            vector = self.model.encode([request.text])[0]
            
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
            raise
    
    async def generate_batch_embeddings(self, request: BatchEmbeddingRequest) -> EmbeddingBatch:
        try:
            vectors = self.model.encode(request.texts)
            batch = EmbeddingBatch(
                dataset_id=request.dataset_id,
                metadata=request.metadata
            )
            
            for i, text in enumerate(request.texts):
                embedding = Embedding(
                    id=uuid.uuid4(),
                    vector=vectors[i],
                    text=text,
                    dataset_id=request.dataset_id,
                    row_id=request.row_ids[i],
                    metadata= {
                        'id': str(request.row_ids[i]),
                    },
                    created_at=datetime.now()
                )
                batch.add_embedding(embedding)
            
            return batch
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {str(e)}")
            raise
    
    async def save_embedding(self, embedding: Embedding) -> Embedding:
        try:
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
            client = await self.get_chroma_client()            
            collection_name = self._get_dataset_collection_name(batch.dataset_id)
            collection = get_or_create_collection(client, collection_name)
            
            # Prepare data for batch import
            ids = [str(embedding.id) for embedding in batch.embeddings]
            embeddings = [embedding.vector.tolist() for embedding in batch.embeddings]
            metadatas = [{
                "dataset_id": str(embedding.dataset_id),
                "row_id": str(embedding.row_id),
                "model_name": self.model_name,
                "created_at": embedding.created_at.isoformat(),
                **{k: str(v) if isinstance(v, (UUID, datetime)) else v for k, v in embedding.metadata.items()}
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
        try:
            client = await self.get_chroma_client()
            
            collection_name = self._get_dataset_collection_name(request.dataset_id)
            collections = client.list_collections()
            
            if collection_name not in collections:
                raise DatasetNotFoundError(request.dataset_id)
            
            collection = client.get_collection(collection_name)
            
            result = collection.get(
                ids=[str(request.embedding_id)],
                include=["embeddings", "documents", "metadatas"]
            )
            
            if not result["ids"]:
                return None
            
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
            raise DatasetNotFoundError(request.dataset_id)
        except Exception as e:
            logger.error(f"Error getting embedding: {str(e)}")
            raise VectorDBError(f"Failed to get embedding: {str(e)}", "chromadb", e)
    
    async def list_embeddings(self, request: ListEmbeddingsRequest) -> List[Embedding]:
        try:
            client = await self.get_chroma_client()
            collection_name = self._get_dataset_collection_name(request.dataset_id)
            
            # Mejorar la verificación de existencia de colección
            try:
                collections = client.list_collections()
                collection_names = [col.name for col in collections]
                logger.debug(f"Available collections: {collection_names}")
                
                if collection_name not in collection_names:
                    logger.info(f"Collection {collection_name} not found in available collections")
                    raise DatasetNotFoundError(request.dataset_id)
                    
            except DatasetNotFoundError:
                raise
            except Exception as list_err:
                logger.warning(f"Error listing collections: {str(list_err)}")
                # Continuar con get_collection como fallback

            # Intentar obtener la colección
            try:
                collection = client.get_collection(collection_name)
            except ValueError as ve:
                logger.info(f"Collection {collection_name} not found (ValueError): {str(ve)}")
                raise DatasetNotFoundError(request.dataset_id)
            except Exception as e:
                logger.error(f"Error getting collection {collection_name}: {type(e).__name__}: {str(e)}")
                raise DatasetNotFoundError(request.dataset_id)

            where = {"dataset_id": request.dataset_id}
            if request.filter_criteria:
                for key, value in request.filter_criteria.items():
                    where[key] = value
            
            try:
                result = collection.get(
                    include=["embeddings", "documents", "metadatas"],
                    where=where
                )
            except Exception as e:
                logger.warning(f"Error with where clause, trying without: {str(e)}")
                result = collection.get(
                    include=["embeddings", "documents", "metadatas"]
                )
            
            if not result["ids"]:
                return []
                
            start = request.offset
            end = start + request.limit
            
            total_items = len(result["ids"])
            if start >= total_items:
                return []
                
            end = min(end, total_items)
            paginated_ids = result["ids"][start:end]
            
            if not paginated_ids:
                return []
            
            paginated_result = collection.get(
                ids=paginated_ids,
                include=["embeddings", "documents", "metadatas"]
            )
            
            embeddings = []
            for i, embedding_id in enumerate(paginated_result["ids"]):
                metadata = {}
                if "metadatas" in paginated_result and paginated_result["metadatas"] and i < len(paginated_result["metadatas"]):
                    metadata = paginated_result["metadatas"][i]

                vector = np.array(paginated_result["embeddings"][i])
                
                text = ""
                if "documents" in paginated_result and paginated_result["documents"] and i < len(paginated_result["documents"]):
                    text = paginated_result["documents"][i]
                
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
            raise DatasetNotFoundError(request.dataset_id)
        except Exception as e:
            logger.error(f"Error listing embeddings: {str(e)}")
            raise VectorDBError(f"Failed to list embeddings: {str(e)}", "chromadb", e)
    
    async def delete_embedding(self, request: DeleteEmbeddingRequest) -> bool:
        try:
            client = await self.get_chroma_client()
            collection_name = self._get_dataset_collection_name(request.dataset_id)
            collections = client.list_collections()
            
            if collection_name not in collections:
                raise DatasetNotFoundError(request.dataset_id)
            
            collection = client.get_collection(collection_name)
            collection.delete(ids=[str(request.embedding_id)])
            
            return True
        except DatasetNotFoundError:
            raise DatasetNotFoundError(request.dataset_id)
        except Exception as e:
            raise VectorDBError(f"Failed to delete embedding: {str(e)}", "chromadb", e)
    
    async def delete_dataset_embeddings(self, dataset_id: str) -> int:
        try:
            client = await self.get_chroma_client()
            collection_name = self._get_dataset_collection_name(dataset_id)
            collections = client.list_collections()
            
            if collection_name not in collections:
                return 0
            
            collection = client.get_collection(collection_name)
            
            count = collection.count()
            collection.delete()
            
            return count
        except Exception as e:
            logger.error(f"Error deleting dataset embeddings: {str(e)}")
            raise VectorDBError(f"Failed to delete dataset embeddings: {str(e)}", "chromadb", e)
    
    async def get_models(self) -> List[EmbeddingModel]:
        return [
            EmbeddingModel(
                name=self.model_name,
                dimension=self.model.get_sentence_embedding_dimension(),
                metadata={"type": "sentence-transformers"}
            )
        ]
    
    async def get_model(self, model_name: str) -> Optional[EmbeddingModel]:
        if model_name != self.model_name:
            return None
        
        return EmbeddingModel(
            name=self.model_name,
            dimension=self.model.get_sentence_embedding_dimension(),
            metadata={"type": "sentence-transformers"}
        )
