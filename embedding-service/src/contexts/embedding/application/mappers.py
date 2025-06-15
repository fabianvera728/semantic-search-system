from typing import List, Optional, Dict, Any
import numpy as np
from uuid import UUID

from ..domain import (
    Embedding,
    Dataset,
    EmbeddingModel,
    EmbeddingResult,
    GenerateEmbeddingRequest,
    BatchEmbeddingRequest,
    DeleteEmbeddingRequest,
    GetEmbeddingRequest,
    ListEmbeddingsRequest,
    CreateDatasetRequest,
    ProcessDatasetRowsRequest,
    EmbeddingPromptTemplate,
    EmbeddingPromptStrategy
)
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
    EmbeddingModelDTO,
    EmbeddingPromptTemplateDTO,
    EmbeddingPromptStrategyDTO
)


# Mappers para Prompt Templates y Strategies
def prompt_template_dto_to_domain(dto: EmbeddingPromptTemplateDTO) -> EmbeddingPromptTemplate:
    """Convert DTO to domain EmbeddingPromptTemplate."""
    return EmbeddingPromptTemplate(
        template=dto.template,
        description=dto.description,
        field_mappings=dto.field_mappings or {},
        metadata=dto.metadata or {}
    )


def prompt_strategy_dto_to_domain(dto: EmbeddingPromptStrategyDTO) -> EmbeddingPromptStrategy:
    """Convert DTO to domain EmbeddingPromptStrategy."""
    prompt_template = None
    if dto.prompt_template:
        prompt_template = prompt_template_dto_to_domain(dto.prompt_template)
    
    return EmbeddingPromptStrategy(
        strategy_type=dto.strategy_type,
        simple_prompt=dto.simple_prompt,
        prompt_template=prompt_template
    )


def prompt_template_to_dto(template: EmbeddingPromptTemplate) -> EmbeddingPromptTemplateDTO:
    """Convert domain EmbeddingPromptTemplate to DTO."""
    return EmbeddingPromptTemplateDTO(
        template=template.template,
        description=template.description,
        field_mappings=template.field_mappings,
        metadata=template.metadata
    )


def prompt_strategy_to_dto(strategy: EmbeddingPromptStrategy) -> EmbeddingPromptStrategyDTO:
    """Convert domain EmbeddingPromptStrategy to DTO."""
    prompt_template_dto = None
    if strategy.prompt_template:
        prompt_template_dto = prompt_template_to_dto(strategy.prompt_template)
    
    return EmbeddingPromptStrategyDTO(
        strategy_type=strategy.strategy_type,
        simple_prompt=strategy.simple_prompt,
        prompt_template=prompt_template_dto
    )


def dict_to_prompt_strategy_dto(data: Dict[str, Any]) -> EmbeddingPromptStrategyDTO:
    """Convert a dict (from event) to EmbeddingPromptStrategyDTO."""
    prompt_template_dto = None
    if data.get('prompt_template'):
        template_data = data['prompt_template']
        prompt_template_dto = EmbeddingPromptTemplateDTO(
            template=template_data.get('template', ''),
            description=template_data.get('description', ''),
            field_mappings=template_data.get('field_mappings', {}),
            metadata=template_data.get('metadata', {})
        )
    
    return EmbeddingPromptStrategyDTO(
        strategy_type=data.get('strategy_type', 'concatenate'),
        simple_prompt=data.get('simple_prompt'),
        prompt_template=prompt_template_dto
    )


# Domain to DTO mappers
def embedding_to_dto(embedding: Embedding, include_vector: bool = True) -> EmbeddingDTO:
    """Convert a domain Embedding to an EmbeddingDTO."""
    vector = None
    if include_vector and embedding.vector is not None:
        vector = embedding.vector.tolist()
    
    return EmbeddingDTO(
        embedding_id=embedding.id,
        dataset_id=embedding.dataset_id,
        row_id=embedding.row_id,
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        dimension=embedding.vector.shape[0] if embedding.vector is not None else 0,
        created_at=embedding.created_at,
        vector=vector,
        metadata=embedding.metadata,
        text=embedding.text
    )


def embedding_result_to_dto(result: EmbeddingResult) -> EmbeddingResultDTO:
    """Convert a domain EmbeddingResult to an EmbeddingResultDTO."""
    return EmbeddingResultDTO(
        embedding_id=result.embedding_id,
        dataset_id=result.dataset_id,
        row_id=result.row_id,
        model_name=result.model_name,
        dimension=result.dimension,
        created_at=result.created_at,
        status=result.status,
        error_message=result.error_message
    )


def dataset_to_dto(dataset: Dataset) -> DatasetDTO:
    """Convert a domain Dataset to a DatasetDTO."""
    dimension = 384
    if dataset.metadata and 'dimension' in dataset.metadata:
        dimension = dataset.metadata['dimension']
        
    return DatasetDTO(
        dataset_id=dataset.id,
        name=dataset.name,
        dimension=dimension,
        embedding_count=dataset.embedding_count,
        created_at=dataset.created_at,
        updated_at=dataset.updated_at,
        metadata=dataset.metadata
    )


def embedding_model_to_dto(model: EmbeddingModel) -> EmbeddingModelDTO:
    """Convert a domain EmbeddingModel to an EmbeddingModelDTO."""
    return EmbeddingModelDTO(
        name=model.name,
        dimension=model.dimension,
        description=model.description
    )


# DTO to Domain mappers
def generate_embedding_request_dto_to_domain(dto: GenerateEmbeddingRequestDTO) -> GenerateEmbeddingRequest:
    """Convert a GenerateEmbeddingRequestDTO to a domain GenerateEmbeddingRequest."""
    return GenerateEmbeddingRequest(
        text=dto.text,
        dataset_id=dto.dataset_id,
        row_id=dto.row_id,
        model_name=dto.model_name
    )


def batch_embedding_request_dto_to_domain(dto: BatchEmbeddingRequestDTO) -> BatchEmbeddingRequest:
    """Convert a BatchEmbeddingRequestDTO to a domain BatchEmbeddingRequest."""
    return BatchEmbeddingRequest(
        texts=dto.texts,
        dataset_id=dto.dataset_id,
        row_ids=dto.row_ids,
        model_name=dto.model_name,
        batch_size=dto.batch_size
    )


def delete_embedding_request_dto_to_domain(dto: DeleteEmbeddingRequestDTO) -> DeleteEmbeddingRequest:
    """Convert a DeleteEmbeddingRequestDTO to a domain DeleteEmbeddingRequest."""
    return DeleteEmbeddingRequest(
        embedding_id=dto.embedding_id,
        dataset_id=dto.dataset_id or ""
    )


def get_embedding_request_dto_to_domain(dto: GetEmbeddingRequestDTO) -> GetEmbeddingRequest:
    """Convert a GetEmbeddingRequestDTO to a domain GetEmbeddingRequest."""
    return GetEmbeddingRequest(
        embedding_id=dto.embedding_id,
        dataset_id=dto.dataset_id or ""
    )


def list_embeddings_request_dto_to_domain(dto: ListEmbeddingsRequestDTO) -> ListEmbeddingsRequest:
    """Convert a ListEmbeddingsRequestDTO to a domain ListEmbeddingsRequest."""
    return ListEmbeddingsRequest(
        dataset_id=dto.dataset_id,
        limit=dto.limit,
        offset=dto.offset
    )


def create_dataset_request_dto_to_domain(dto: CreateDatasetRequestDTO) -> CreateDatasetRequest:
    """Convert a CreateDatasetRequestDTO to a domain CreateDatasetRequest."""
    return CreateDatasetRequest(
        dataset_id=dto.dataset_id or "",
        name=dto.name,
        dimension=dto.dimension,
        metadata=dto.metadata or {}
    )


def process_dataset_rows_request_dto_to_domain(dto: ProcessDatasetRowsRequestDTO) -> ProcessDatasetRowsRequest:
    """Convert a ProcessDatasetRowsRequestDTO to a domain ProcessDatasetRowsRequest."""
    prompt_strategy = None
    if dto.prompt_strategy:
        prompt_strategy = prompt_strategy_dto_to_domain(dto.prompt_strategy)
    
    return ProcessDatasetRowsRequest(
        dataset_id=dto.dataset_id,
        rows=dto.rows,
        model_name=dto.model_name,
        text_fields=dto.text_fields,
        batch_size=dto.batch_size,
        prompt_strategy=prompt_strategy
    )


# ===== BACKWARDS COMPATIBILITY ALIASES =====
# Mantener los nombres antiguos para compatibilidad con imports existentes

def generate_embedding_dto_to_domain(dto: GenerateEmbeddingRequestDTO) -> GenerateEmbeddingRequest:
    """Alias for backwards compatibility."""
    return generate_embedding_request_dto_to_domain(dto)


def batch_embedding_dto_to_domain(dto: BatchEmbeddingRequestDTO) -> BatchEmbeddingRequest:
    """Alias for backwards compatibility."""
    return batch_embedding_request_dto_to_domain(dto)


def delete_embedding_dto_to_domain(dto: DeleteEmbeddingRequestDTO) -> DeleteEmbeddingRequest:
    """Alias for backwards compatibility."""
    return delete_embedding_request_dto_to_domain(dto)


def get_embedding_dto_to_domain(dto: GetEmbeddingRequestDTO) -> GetEmbeddingRequest:
    """Alias for backwards compatibility."""
    return get_embedding_request_dto_to_domain(dto)


def list_embeddings_dto_to_domain(dto: ListEmbeddingsRequestDTO) -> ListEmbeddingsRequest:
    """Alias for backwards compatibility."""
    return list_embeddings_request_dto_to_domain(dto)


def create_dataset_dto_to_domain(dto: CreateDatasetRequestDTO) -> CreateDatasetRequest:
    """Alias for backwards compatibility."""
    return create_dataset_request_dto_to_domain(dto)


def process_dataset_rows_dto_to_domain(dto: ProcessDatasetRowsRequestDTO) -> ProcessDatasetRowsRequest:
    """Alias for backwards compatibility."""
    return process_dataset_rows_request_dto_to_domain(dto)


def embeddings_to_dtos(embeddings: List[Embedding], include_vectors: bool = True) -> List[EmbeddingDTO]:
    return [embedding_to_dto(embedding, include_vectors) for embedding in embeddings]


def embedding_results_to_dtos(results: List[EmbeddingResult]) -> List[EmbeddingResultDTO]:
    """Convert a list of domain EmbeddingResults to a list of EmbeddingResultDTOs."""
    return [embedding_result_to_dto(result) for result in results]


def datasets_to_dtos(datasets: List[Dataset]) -> List[DatasetDTO]:
    """Convert a list of domain Datasets to a list of DatasetDTOs."""
    return [dataset_to_dto(dataset) for dataset in datasets]


def embedding_models_to_dtos(models: List[EmbeddingModel]) -> List[EmbeddingModelDTO]:
    """Convert a list of domain EmbeddingModels to a list of EmbeddingModelDTOs."""
    return [embedding_model_to_dto(model) for model in models] 