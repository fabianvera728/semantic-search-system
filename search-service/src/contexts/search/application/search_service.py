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
    
    def __init__(
        self, 
        search_repository: SearchRepository,
        embedding_repository: EmbeddingRepository
    ):
        self.search_repository = search_repository
        self.embedding_repository = embedding_repository

    async def search(
        self, 
        query: str, 
        dataset_id: str, 
        limit: int = 10,
        search_type: str = "semantic",
        embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        hybrid_alpha: float = 0.5,
        additional_params: Optional[Dict[str, Any]] = None
    ) -> SearchResults:
        """Realiza una búsqueda"""
        # Preprocesamiento de la consulta
        clean_query = self._preprocess_query(query)
        
        # Expansión de consulta si está habilitada en los parámetros adicionales
        expanded_query = clean_query
        if additional_params and additional_params.get("expand_query", False):
            expanded_query = await self._expand_query(clean_query, additional_params.get("expansion_terms", []))
            logger.info(f"Consulta expandida: '{clean_query}' -> '{expanded_query}'")
        
        # Crear objetos de valor
        search_query = SearchQuery(text=expanded_query)
        dataset_id_vo = DatasetId(value=dataset_id)
        
        # Procesar parámetros adicionales
        processed_params = additional_params or {}
        # Añadir información de la consulta original y expandida a los parámetros
        processed_params["original_query"] = query
        processed_params["clean_query"] = clean_query
        processed_params["expanded_query"] = expanded_query
        
        # Configurar búsqueda
        search_config = SearchConfig(
            limit=limit,
            embedding_model=embedding_model,
            search_type=search_type,
            hybrid_alpha=hybrid_alpha,
            additional_params=processed_params
        )
        
        request = SearchRequest(
            query=search_query,
            dataset_id=dataset_id_vo,
            config=search_config
        )
        
        return await self.search_repository.search(request)
    
    def _preprocess_query(self, query: str) -> str:
        """Preprocesa la consulta para mejorar resultados"""
        if not query:
            return ""
            
        # Eliminar espacios extras al inicio y final
        clean_query = query.strip()
        
        # Normalizar espacios múltiples
        clean_query = ' '.join(clean_query.split())
        
        # Normalizar caracteres acentuados para búsquedas más consistentes
        clean_query = self._normalize_accents(clean_query)
        
        return clean_query
    
    def _normalize_accents(self, text: str) -> str:
        """Normaliza los acentos en el texto para mejorar coincidencias"""
        import unicodedata
        # Normalización NFKD para separar caracteres base y combinados
        normalized = unicodedata.normalize('NFKD', text)
        # Mantener el texto original pero normalizado
        return normalized
    
    async def _expand_query(self, query: str, custom_terms: List[str] = None) -> str:
        """Expande la consulta con términos relevantes de forma genérica"""
        # Si hay términos personalizados, utilizarlos directamente
        if custom_terms and len(custom_terms) > 0:
            # Filtrar términos vacíos y duplicados
            filtered_terms = []
            query_lower = query.lower()
            
            for term in custom_terms:
                term = term.strip()
                if term and term.lower() not in query_lower and term not in filtered_terms:
                    filtered_terms.append(term)
            
            # Si hay términos filtrados, añadirlos a la consulta
            if filtered_terms:
                expanded_query = f"{query} {' '.join(filtered_terms)}"
                return expanded_query
        
        # Si no hay términos personalizados, devolver la consulta original
        return query
    
    async def get_dataset_embeddings(self, dataset_id: str) -> EmbeddingCollection:
        """Obtiene los embeddings para un dataset"""
        return await self.search_repository.get_dataset_embeddings(dataset_id)
    
    async def generate_embeddings(
        self, 
        texts: List[str], 
        model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
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