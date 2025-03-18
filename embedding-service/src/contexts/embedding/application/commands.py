from typing import Dict, List, Any, Optional, Callable, Awaitable, Union, Type
import logging
from uuid import UUID

from .controllers import CommandController, CommandResult
from .embedding_service import EmbeddingService
from .dtos import (
    EmbeddingDTO,
    EmbeddingResultDTO,
    DatasetDTO,
    GenerateEmbeddingRequestDTO,
    BatchEmbeddingRequestDTO,
    DeleteEmbeddingRequestDTO,
    GetEmbeddingRequestDTO,
    ListEmbeddingsRequestDTO,
    CreateDatasetRequestDTO,
    ProcessDatasetRowsRequestDTO,
    EmbeddingModelDTO
)
from .mappers import (
    embedding_to_dto,
    embedding_result_to_dto,
    dataset_to_dto,
    embedding_model_to_dto,
    embeddings_to_dtos,
    embedding_results_to_dtos,
    datasets_to_dtos,
    embedding_models_to_dtos,
    generate_embedding_dto_to_domain,
    batch_embedding_dto_to_domain,
    delete_embedding_dto_to_domain,
    get_embedding_dto_to_domain,
    list_embeddings_dto_to_domain,
    create_dataset_dto_to_domain,
    process_dataset_rows_dto_to_domain
)

logger = logging.getLogger(__name__)


class CommandHandlers:
    """Command handlers for the embedding service."""
    
    def __init__(self, embedding_service: EmbeddingService):
        self.embedding_service = embedding_service
        self._init_controllers()
    
    def _init_controllers(self) -> None:
        """Initialize all command controllers."""
        self.generate_embedding_controller = CommandController(
            input_type=GenerateEmbeddingRequestDTO,
            handler=self.handle_generate_embedding
        )
        
        self.generate_batch_embeddings_controller = CommandController(
            input_type=BatchEmbeddingRequestDTO,
            handler=self.handle_generate_batch_embeddings
        )
        
        self.process_dataset_rows_controller = CommandController(
            input_type=ProcessDatasetRowsRequestDTO,
            handler=self.handle_process_dataset_rows
        )
        
        self.get_embedding_controller = CommandController(
            input_type=GetEmbeddingRequestDTO,
            handler=self.handle_get_embedding
        )
        
        self.delete_embedding_controller = CommandController(
            input_type=DeleteEmbeddingRequestDTO,
            handler=self.handle_delete_embedding
        )
        
        self.list_embeddings_controller = CommandController(
            input_type=ListEmbeddingsRequestDTO,
            handler=self.handle_list_embeddings
        )
        
        self.create_dataset_controller = CommandController(
            input_type=CreateDatasetRequestDTO,
            handler=self.handle_create_dataset
        )
    
    async def handle_generate_embedding(
        self, dto: GenerateEmbeddingRequestDTO
    ) -> EmbeddingResultDTO:
        """Handle a request to generate a single embedding."""
        domain_request = generate_embedding_dto_to_domain(dto)
        result = await self.embedding_service.generate_embedding(domain_request)
        return embedding_result_to_dto(result)
    
    async def handle_generate_batch_embeddings(
        self, dto: BatchEmbeddingRequestDTO
    ) -> List[EmbeddingResultDTO]:
        """Handle a request to generate batch embeddings."""
        domain_request = batch_embedding_dto_to_domain(dto)
        results = await self.embedding_service.generate_batch_embeddings(domain_request)
        return embedding_results_to_dtos(results)
    
    async def handle_process_dataset_rows(
        self, dto: ProcessDatasetRowsRequestDTO
    ) -> Dict[str, Any]:
        """Handle a request to process dataset rows."""
        domain_request = process_dataset_rows_dto_to_domain(dto)
        result = await self.embedding_service.process_dataset_rows(domain_request)
        return result
    
    async def handle_get_embedding(
        self, dto: GetEmbeddingRequestDTO
    ) -> EmbeddingDTO:
        """Handle a request to get an embedding."""
        domain_request = get_embedding_dto_to_domain(dto)
        embedding = await self.embedding_service.get_embedding(domain_request)
        return embedding_to_dto(embedding, dto.include_vector)
    
    async def handle_delete_embedding(
        self, dto: DeleteEmbeddingRequestDTO
    ) -> Dict[str, Any]:
        """Handle a request to delete an embedding."""
        domain_request = delete_embedding_dto_to_domain(dto)
        result = await self.embedding_service.delete_embedding(domain_request)
        return {"deleted": result, "embedding_id": str(dto.embedding_id)}
    
    async def handle_list_embeddings(
        self, dto: ListEmbeddingsRequestDTO
    ) -> Dict[str, Any]:
        """Handle a request to list embeddings."""
        domain_request = list_embeddings_dto_to_domain(dto)
        embeddings = await self.embedding_service.list_embeddings(domain_request)
        embedding_dtos = embeddings_to_dtos(embeddings, dto.include_vectors)
        
        return {
            "dataset_id": dto.dataset_id,
            "count": len(embedding_dtos),
            "embeddings": embedding_dtos,
            "offset": dto.offset,
            "limit": dto.limit
        }
    
    async def handle_create_dataset(
        self, dto: CreateDatasetRequestDTO
    ) -> DatasetDTO:
        """Handle a request to create a dataset."""
        domain_request = create_dataset_dto_to_domain(dto)
        dataset = await self.embedding_service.dataset_repository.create_dataset(domain_request)
        return dataset_to_dto(dataset)
    
    async def handle_get_dataset(
        self, dataset_id: str
    ) -> DatasetDTO:
        """Handle a request to get a dataset."""
        dataset = await self.embedding_service.get_dataset(dataset_id)
        return dataset_to_dto(dataset)
    
    async def handle_list_datasets(
        self, limit: int = 100, offset: int = 0
    ) -> Dict[str, Any]:
        """Handle a request to list datasets."""
        datasets = await self.embedding_service.list_datasets(limit, offset)
        dataset_dtos = datasets_to_dtos(datasets)
        
        return {
            "count": len(dataset_dtos),
            "datasets": dataset_dtos,
            "offset": offset,
            "limit": limit
        }
    
    async def handle_delete_dataset(
        self, dataset_id: str
    ) -> Dict[str, Any]:
        """Handle a request to delete a dataset."""
        result = await self.embedding_service.delete_dataset(dataset_id)
        return {"deleted": result, "dataset_id": dataset_id}
    
    async def handle_get_embedding_models(self) -> Dict[str, Any]:
        """Handle a request to get available embedding models."""
        models = await self.embedding_service.get_embedding_models()
        model_dtos = embedding_models_to_dtos(models)
        
        return {
            "count": len(model_dtos),
            "models": model_dtos
        } 