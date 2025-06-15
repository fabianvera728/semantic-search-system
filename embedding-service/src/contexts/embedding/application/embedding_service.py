import logging
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
import time
import asyncio
from datetime import datetime

from ..domain import (
    EmbeddingRepository,
    DatasetRepository,
    Embedding,
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
    InvalidRequestError
)

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(
        self,
        embedding_repository: EmbeddingRepository,
        dataset_repository: DatasetRepository,
    ):
        self.embedding_repository = embedding_repository
        self.dataset_repository = dataset_repository
    
    async def generate_embedding(self, request: GenerateEmbeddingRequest) -> EmbeddingResult:
        """Generate a single embedding"""
        start_time = time.time()
        
        try:
            embedding = await self.embedding_repository.generate_embedding(request)
            await self.embedding_repository.save_embedding(embedding)
            
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
        start_time = time.time()
        dataset_id = request.dataset_id
        rows = request.rows or []
        
        try:
            dataset = await self.dataset_repository.get_dataset(dataset_id)
            text_fields = request.text_fields or []
            
            # La prompt strategy ahora viene directamente en el request desde el evento
            prompt_strategy = request.prompt_strategy
            
            if not text_fields and rows:
                sample_row = rows[0]
                
                for field, value in sample_row.items():
                    if isinstance(value, str) and field != "id" and len(value.strip()) > 0:
                        text_fields.append(field)
            
            if not text_fields and not prompt_strategy:
                return {
                    "success": False,
                    "processed": 0,
                    "errors": 0,
                    "message": "No text fields found and no prompt strategy available"
                }
        
        except Exception as e:
            dataset = None
            prompt_strategy = request.prompt_strategy
            rows = []
        
        results = []
        errors = 0
        
        for i in range(0, len(rows), request.batch_size):
            batch_rows = rows[i:i+request.batch_size]
            
            try:
                texts = []
                row_ids = []
                
                for row in batch_rows:
                    if not row or not isinstance(row, dict):
                        continue
                    
                    row_id = row.get("id")
                    if not row_id:
                        continue
                    
                    # Nueva funcionalidad: usar prompt strategy si está disponible
                    if prompt_strategy:
                        text_content = self._generate_contextual_content(row, request)
                    else:
                        # Lógica existente como fallback
                        if request.text_fields:
                            text_content = " ".join([
                                str(row.get(field, "")) 
                                for field in request.text_fields 
                                if field in row and row.get(field)
                            ])
                        else:
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
                    
                    max_retries = 3
                    retry_count = 0
                    
                    while retry_count < max_retries:
                        try:
                            batch_results = await self.generate_batch_embeddings(batch_request)
                            results.extend(batch_results)
                            break
                        except Exception as batch_error:
                            retry_count += 1
                            if retry_count >= max_retries:
                                raise
                            
                            retry_delay = 0.5 * (2 ** (retry_count - 1))
                            logger.warning(f"Retry {retry_count}/{max_retries} for batch embeddings: {str(batch_error)}. Retrying in {retry_delay}s...")
                            await asyncio.sleep(retry_delay)
            
            except Exception as batch_process_err:
                logger.error(f"Error processing batch: {str(batch_process_err)}")
                errors += len(batch_rows)
        
        if dataset:
            try:
                dataset.embedding_count = len(results)
                dataset.updated_at = datetime.now()
                await self.dataset_repository.update_dataset(dataset)
                logger.info(f"Updated dataset stats: {dataset.id}, embedding count: {dataset.embedding_count}")
            except Exception as update_err:
                logger.warning(f"Error updating dataset stats: {str(update_err)}")
        
        execution_time = time.time() - start_time
        
        return {
            "success": len(results) > 0,
            "dataset_id": request.dataset_id,
            "processed_rows": len(rows),
            "embeddings_created": len(results),
            "errors": errors,
            "execution_time_seconds": execution_time,
            "model_name": request.model_name
        }
    
    async def _get_or_create_dataset(self, dataset_id: str, dataset_info: Dict[str, Any], model_name: str) -> Optional[Dataset]:
        dataset = None
        
        try:
            dataset = await self.dataset_repository.get_dataset(dataset_id)
            if dataset:
                logger.info(f"Found dataset in repository: {dataset_id}")
                return dataset
        except Exception as e:
            logger.warning(f"Dataset not found in repository: {str(e)}")
        
        try:
            from src.contexts.embedding.infrastructure.repositories.chroma_dataset_repository import ChromaDatasetRepository
            if isinstance(self.dataset_repository, ChromaDatasetRepository):
                chroma_repo = self.dataset_repository
                client = await chroma_repo.get_chroma_client()
                
                collection_name = chroma_repo._get_dataset_collection_name(dataset_id)
                try:
                    collection = client.get_collection(collection_name)
                    logger.info(f"Found dataset collection in ChromaDB: {collection_name}")
                    
                    dataset = Dataset(
                        id=dataset_id,
                        name=dataset_info.get("name", f"Dataset {dataset_id}"),
                        created_at=datetime.now(),
                        updated_at=datetime.now(),
                        embedding_count=0,
                        metadata=collection.metadata or {}
                    )
                    logger.info(f"Created virtual dataset from ChromaDB collection: {dataset.id}")
                    return dataset
                except Exception as coll_err:
                    logger.warning(f"Collection not found in ChromaDB: {str(coll_err)}")
        except Exception as chroma_err:
            logger.warning(f"Error accessing ChromaDB: {str(chroma_err)}")
        
        try:
            model = await self.embedding_repository.get_model(model_name)
            if not model:
                model = EmbeddingModel(
                    name=model_name,
                    dimension=384 
                )
            
            create_dataset_request = CreateDatasetRequest(
                dataset_id=dataset_id,
                name=dataset_info.get("name", f"Dataset {dataset_id}"),
                dimension=model.dimension
            )
            
            logger.info(f"Creating new dataset in embedding storage: {dataset_id}")
            dataset = await self.dataset_repository.create_dataset(create_dataset_request)
            logger.info(f"Successfully created dataset: {dataset_id}")
            return dataset
        except Exception as create_err:
            logger.error(f"Failed to create dataset: {str(create_err)}")
        
        return None
    
    def _convert_dict_to_prompt_strategy(self, prompt_strategy_data: Dict[str, Any]):
        """Convierte un dict de prompt strategy a domain object"""
        from ..domain.value_objects import EmbeddingPromptStrategy, EmbeddingPromptTemplate
        
        prompt_template = None
        if prompt_strategy_data.get('prompt_template'):
            template_data = prompt_strategy_data['prompt_template']
            prompt_template = EmbeddingPromptTemplate(
                template=template_data.get('template', ''),
                description=template_data.get('description', ''),
                field_mappings=template_data.get('field_mappings', {}),
                metadata=template_data.get('metadata', {})
            )
        
        return EmbeddingPromptStrategy(
            strategy_type=prompt_strategy_data.get('strategy_type', 'concatenate'),
            simple_prompt=prompt_strategy_data.get('simple_prompt'),
            prompt_template=prompt_template
        )
    
    def _generate_contextual_content(self, row_data: Dict[str, Any], request: ProcessDatasetRowsRequest) -> str:
        """Genera contenido contextualizado usando la estrategia de prompt configurada"""
        if not request.prompt_strategy:
            return ""
        
        try:
            content = request.prompt_strategy.generate_content(row_data, request.text_fields)
            logger.debug(f"Generated contextual content for row {row_data.get('id', 'unknown')}: {content[:100]}...")
            return content
        except Exception as e:
            logger.error(f"Error generating contextual content: {str(e)}")
            # Fallback a concatenación simple si hay error
            if request.text_fields:
                return " ".join([
                    str(row_data.get(field, "")) 
                    for field in request.text_fields 
                    if field in row_data and row_data.get(field)
                ])
            else:
                return " ".join([
                    str(value) 
                    for key, value in row_data.items() 
                    if isinstance(value, str) and key != "id" and value
                ])
    
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
        dataset = await self.dataset_repository.get_dataset(dataset_id)
        if not dataset:
            raise DatasetNotFoundError(dataset_id)
        
        deleted_count = await self.embedding_repository.delete_dataset_embeddings(dataset_id)
        
        result = await self.dataset_repository.delete_dataset(dataset_id)
        return result 