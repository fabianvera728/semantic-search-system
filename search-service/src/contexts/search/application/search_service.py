import logging
from typing import List, Dict, Any, Optional
from uuid import UUID

from ..domain.repositories import SearchRepository, EmbeddingRepository
from ..domain.entities import SearchResults, EmbeddingCollection
from ..domain.value_objects import (
    SearchRequest, 
    SearchQuery, 
    DatasetId, 
    SearchConfig,
    SearchId,
    EmbeddingRequest
)

logger = logging.getLogger(__name__)


class SearchService:
    """Servicio de búsqueda"""
    
    def __init__(
        self, 
        search_repository: SearchRepository,
        embedding_repository: EmbeddingRepository
    ):
        """Inicializa el servicio de búsqueda"""
        self.search_repository = search_repository
        self.embedding_repository = embedding_repository
        
        logger.info("Servicio de búsqueda inicializado")
    
    async def search(
        self, 
        query: str, 
        dataset_id: str, 
        limit: int = 10,
        search_type: str = "semantic",
        embedding_model: str = "sentence-transformer/all-MiniLM-L6-v2",
        hybrid_alpha: float = 0.5,
        additional_params: Optional[Dict[str, Any]] = None
    ) -> SearchResults:
        """Realiza una búsqueda"""
        # Crear objetos de valor
        search_query = SearchQuery(text=query)
        dataset_id_vo = DatasetId(value=dataset_id)
        search_config = SearchConfig(
            limit=limit,
            embedding_model=embedding_model,
            search_type=search_type,
            hybrid_alpha=hybrid_alpha,
            additional_params=additional_params or {}
        )
        
        # Crear solicitud de búsqueda
        request = SearchRequest(
            query=search_query,
            dataset_id=dataset_id_vo,
            config=search_config
        )
        
        # Realizar búsqueda
        return await self.search_repository.search(request)
    
    async def get_dataset_embeddings(self, dataset_id: str) -> EmbeddingCollection:
        """Obtiene los embeddings para un dataset"""
        return await self.search_repository.get_dataset_embeddings(dataset_id)
    
    async def generate_embeddings(
        self, 
        texts: List[str], 
        model: str = "sentence-transformer/all-MiniLM-L6-v2",
        batch_size: int = 32,
        additional_params: Optional[Dict[str, Any]] = None
    ) -> List[List[float]]:
        """Genera embeddings para una lista de textos"""
        # Crear solicitud de embeddings
        request = EmbeddingRequest(
            texts=texts,
            model=model,
            batch_size=batch_size,
            additional_params=additional_params or {}
        )
        
        # Generar embeddings
        embeddings = await self.embedding_repository.generate_embeddings(request)
        
        # Convertir a lista de listas para serialización JSON
        return embeddings.tolist()
    
    async def get_search_results(self, search_id: str) -> Optional[SearchResults]:
        """Obtiene los resultados de una búsqueda por su ID"""
        return await self.search_repository.get_search_results(search_id)
    
    async def list_available_models(self) -> List[Dict[str, Any]]:
        """Lista todos los modelos de embedding disponibles"""
        return await self.embedding_repository.list_available_models()
    
    async def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """Obtiene información sobre un modelo de embedding"""
        return await self.embedding_repository.get_model_info(model_name) 