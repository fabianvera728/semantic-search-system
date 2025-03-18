import logging
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
import time
import asyncio
from datetime import datetime

from ..domain import (
    EmbeddingRepository,
    DatasetRepository,
    DataStorageRepository,
    Embedding,
    EmbeddingBatch,
    Dataset,
    EmbeddingModel,
    GenerateEmbeddingRequest,
    BatchEmbeddingRequest,
    DeleteEmbeddingRequest,
    GetEmbeddingRequest,
    ListEmbeddingsRequest,
    CreateDatasetRequest,
    ProcessDatasetRowsRequest,
    EmbeddingResult,
    DatasetNotFoundError,
    EmbeddingNotFoundError,
    DataStorageError,
    InvalidRequestError
)

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(
        self,
        embedding_repository: EmbeddingRepository,
        dataset_repository: DatasetRepository,
        data_storage_repository: DataStorageRepository
    ):
        self.embedding_repository = embedding_repository
        self.dataset_repository = dataset_repository
        self.data_storage_repository = data_storage_repository
    
    async def generate_embedding(self, request: GenerateEmbeddingRequest) -> EmbeddingResult:
        """Generate a single embedding"""
        start_time = time.time()
        
        try:
            embedding = await self.embedding_repository.generate_embedding(request)
            await self.embedding_repository.save_embedding(embedding)
            
            execution_time = time.time() - start_time
            logger.info(f"Generated embedding for row {request.row_id} in {execution_time:.2f}s")
            
            return EmbeddingResult(
                embedding_id=embedding.id,
                dataset_id=embedding.dataset_id,
                row_id=embedding.row_id,
                model_name=request.model_name,
                dimension=embedding.vector.shape[0],
                created_at=embedding.created_at,
                status="success"
            )
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            return EmbeddingResult(
                embedding_id=UUID(int=0),
                dataset_id=request.dataset_id,
                row_id=request.row_id,
                model_name=request.model_name,
                dimension=0,
                status="error",
                error_message=str(e)
            )
    
    async def generate_batch_embeddings(self, request: BatchEmbeddingRequest) -> List[EmbeddingResult]:
        """Generate embeddings for a batch of texts"""
        start_time = time.time()
        
        if len(request.texts) != len(request.row_ids):
            raise InvalidRequestError("Number of texts and row_ids must match")
        
        try:
            batch = await self.embedding_repository.generate_batch_embeddings(request)
            await self.embedding_repository.save_batch_embeddings(batch)
            
            execution_time = time.time() - start_time
            logger.info(f"Generated {len(batch.embeddings)} embeddings in {execution_time:.2f}s")
            
            return [
                EmbeddingResult(
                    embedding_id=embedding.id,
                    dataset_id=embedding.dataset_id,
                    row_id=embedding.row_id,
                    model_name=request.model_name,
                    dimension=embedding.vector.shape[0],
                    created_at=embedding.created_at,
                    status="success"
                )
                for embedding in batch.embeddings
            ]
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {str(e)}")
            return [
                EmbeddingResult(
                    embedding_id=UUID(int=0),
                    dataset_id=request.dataset_id,
                    row_id=row_id,
                    model_name=request.model_name,
                    dimension=0,
                    status="error",
                    error_message=str(e)
                )
                for row_id in request.row_ids
            ]
    
    async def process_dataset_rows(self, request: ProcessDatasetRowsRequest) -> Dict[str, Any]:
        """Process rows from a dataset and generate embeddings"""
        start_time = time.time()
        
        # Check if dataset exists
        dataset_info = await self.data_storage_repository.get_dataset_info(request.dataset_id)
        if not dataset_info:
            raise DatasetNotFoundError(request.dataset_id)
        
        # Create dataset in embedding storage if it doesn't exist
        dataset = await self.dataset_repository.get_dataset(request.dataset_id)
        if not dataset:
            # Get model dimension
            model = await self.embedding_repository.get_model(request.model_name)
            if not model:
                model = EmbeddingModel(
                    name=request.model_name,
                    dimension=384  # Default dimension for all-MiniLM-L6-v2
                )
            
            create_dataset_request = CreateDatasetRequest(
                dataset_id=request.dataset_id,
                name=dataset_info.get("name", f"Dataset {request.dataset_id}"),
                dimension=model.dimension
            )
            
            dataset = await self.dataset_repository.create_dataset(create_dataset_request)
        
        # Get rows to process
        if request.row_ids:
            # Process specific rows
            rows = []
            for row_id in request.row_ids:
                row = await self.data_storage_repository.get_dataset_row(request.dataset_id, row_id)
                if row:
                    rows.append(row)
        else:
            # Process all rows with pagination
            rows = await self.data_storage_repository.get_dataset_rows(
                request.dataset_id,
                offset=0,
                limit=request.batch_size
            )
            
            total_rows_processed = len(rows)
            while len(rows) == request.batch_size:
                next_rows = await self.data_storage_repository.get_dataset_rows(
                    request.dataset_id,
                    offset=total_rows_processed,
                    limit=request.batch_size
                )
                
                if not next_rows:
                    break
                    
                rows.extend(next_rows)
                total_rows_processed += len(next_rows)
                
                if total_rows_processed >= 1000:  # Safety limit
                    logger.warning(f"Reached safety limit of 1000 rows for dataset {request.dataset_id}")
                    break
        
        logger.info(f"Processing {len(rows)} rows from dataset {request.dataset_id}")
        
        # Generate and save embeddings
        results = []
        for i in range(0, len(rows), request.batch_size):
            batch_rows = rows[i:i+request.batch_size]
            
            texts = []
            row_ids = []
            
            for row in batch_rows:
                if not row or not isinstance(row, dict):
                    continue
                
                # Extract text fields
                row_id = row.get("id")
                if not row_id:
                    continue
                
                # Process text fields
                if request.text_fields:
                    # Use specific fields
                    text_content = " ".join([
                        str(row.get(field, "")) 
                        for field in request.text_fields 
                        if field in row and row.get(field)
                    ])
                else:
                    # Use all string fields
                    text_content = " ".join([
                        str(value) 
                        for key, value in row.items() 
                        if isinstance(value, str) and key != "id"
                    ])
                
                if text_content.strip():
                    texts.append(text_content)
                    row_ids.append(row_id)
            
            if texts:
                batch_request = BatchEmbeddingRequest(
                    texts=texts,
                    dataset_id=request.dataset_id,
                    row_ids=row_ids,
                    model_name=request.model_name,
                    batch_size=request.batch_size
                )
                
                batch_results = await self.generate_batch_embeddings(batch_request)
                results.extend(batch_results)
        
        # Update dataset stats
        dataset.embedding_count = len(results)
        dataset.updated_at = datetime.now()
        await self.dataset_repository.update_dataset(dataset)
        
        execution_time = time.time() - start_time
        
        return {
            "dataset_id": request.dataset_id,
            "processed_rows": len(rows),
            "embeddings_created": len(results),
            "execution_time_seconds": execution_time,
            "model_name": request.model_name
        }
    
    async def get_embedding(self, request: GetEmbeddingRequest) -> Embedding:
        """Get a single embedding"""
        embedding = await self.embedding_repository.get_embedding(request)
        if not embedding:
            raise EmbeddingNotFoundError(request.embedding_id, request.dataset_id)
        return embedding
    
    async def delete_embedding(self, request: DeleteEmbeddingRequest) -> bool:
        """Delete a single embedding"""
        return await self.embedding_repository.delete_embedding(request)
    
    async def list_embeddings(self, request: ListEmbeddingsRequest) -> List[Embedding]:
        """List embeddings with pagination"""
        return await self.embedding_repository.list_embeddings(request)
    
    async def get_embedding_models(self) -> List[EmbeddingModel]:
        """Get all available embedding models"""
        return await self.embedding_repository.get_models()
    
    async def get_dataset(self, dataset_id: str) -> Dataset:
        """Get dataset information"""
        dataset = await self.dataset_repository.get_dataset(dataset_id)
        if not dataset:
            raise DatasetNotFoundError(dataset_id)
        return dataset
    
    async def list_datasets(self, limit: int = 100, offset: int = 0) -> List[Dataset]:
        """List datasets with pagination"""
        return await self.dataset_repository.list_datasets(limit, offset)
    
    async def delete_dataset(self, dataset_id: str) -> bool:
        """Delete a dataset and all its embeddings"""
        dataset = await self.dataset_repository.get_dataset(dataset_id)
        if not dataset:
            raise DatasetNotFoundError(dataset_id)
        
        # Delete embeddings first
        deleted_count = await self.embedding_repository.delete_dataset_embeddings(dataset_id)
        logger.info(f"Deleted {deleted_count} embeddings from dataset {dataset_id}")
        
        # Delete dataset
        result = await self.dataset_repository.delete_dataset(dataset_id)
        return result 