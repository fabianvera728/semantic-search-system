from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import numpy as np

from .entities import EmbeddingCollection, SearchResults
from .value_objects import SearchRequest, EmbeddingRequest


class EmbeddingRepository(ABC):
    """Interfaz para el repositorio de embeddings"""
    
    @abstractmethod
    async def generate_embeddings(self, request: EmbeddingRequest) -> np.ndarray:
        """Genera embeddings para una lista de textos"""
        pass
    
    @abstractmethod
    async def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """Obtiene información sobre un modelo de embedding"""
        pass
    
    @abstractmethod
    async def list_available_models(self) -> List[Dict[str, Any]]:
        """Lista todos los modelos de embedding disponibles"""
        pass


class SearchRepository(ABC):
    """Interfaz para el repositorio de búsqueda"""
    
    @abstractmethod
    async def search(self, request: SearchRequest) -> SearchResults:
        """Realiza una búsqueda"""
        pass
    
    @abstractmethod
    async def get_dataset_embeddings(self, dataset_id: str) -> EmbeddingCollection:
        """Obtiene los embeddings para un dataset"""
        pass
    
    @abstractmethod
    async def save_search_results(self, results: SearchResults) -> None:
        """Guarda los resultados de una búsqueda"""
        pass
    
    @abstractmethod
    async def get_search_results(self, search_id: str) -> Optional[SearchResults]:
        """Obtiene los resultados de una búsqueda por su ID"""
        pass 