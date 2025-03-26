import logging
import time
import uuid
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Query, Path, status

from ...contexts.search.application import SearchService
from ...contexts.search.domain.exceptions import (
    DatasetNotFoundException,
    EmbeddingModelNotFoundException,
    EmbeddingGenerationException,
    SearchExecutionException,
    InvalidSearchTypeException,
    DataStorageConnectionException,
    EmptyQueryException
)

logger = logging.getLogger(__name__)


# Modelos de datos para la API
class EmbeddingRequest:
    """Solicitud para generar embeddings"""
    def __init__(
        self,
        texts: List[str],
        model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        batch_size: int = 32,
        additional_params: Optional[Dict[str, Any]] = None
    ):
        self.texts = texts
        self.model = model
        self.batch_size = batch_size
        self.additional_params = additional_params or {}


class SearchRequest:
    """Solicitud para realizar una búsqueda"""
    def __init__(
        self,
        query: str,
        dataset_id: str,
        limit: int = 10,
        search_type: str = "semantic",
        embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        hybrid_alpha: float = 0.5,
        additional_params: Optional[Dict[str, Any]] = None
    ):
        self.query = query
        self.dataset_id = dataset_id
        self.limit = limit
        self.search_type = search_type
        self.embedding_model = embedding_model
        self.hybrid_alpha = hybrid_alpha
        self.additional_params = additional_params or {}


class SearchController:
    """Controlador para la API de búsqueda"""
    
    def __init__(self, search_service: SearchService):
        """Inicializa el controlador de búsqueda"""
        self.search_service = search_service
        self.router = APIRouter(prefix="/search", tags=["search"])
        self._register_routes()
        
        logger.info("Controlador de búsqueda inicializado")
    
    def _register_routes(self):
        """Registra las rutas de la API"""
        
        @self.router.post("/embeddings")
        async def generate_embeddings(request: dict):
            """Genera embeddings para una lista de textos"""
            try:
                # Validar solicitud
                if "texts" not in request:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="El campo 'texts' es obligatorio"
                    )
                
                # Crear solicitud
                embedding_request = EmbeddingRequest(
                    texts=request["texts"],
                    model=request.get("model", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"),
                    batch_size=request.get("batch_size", 32),
                    additional_params=request.get("additional_params")
                )
                
                # Generar embeddings
                embeddings = await self.search_service.generate_embeddings(
                    texts=embedding_request.texts,
                    model=embedding_request.model,
                    batch_size=embedding_request.batch_size,
                    additional_params=embedding_request.additional_params
                )
                
                return {
                    "embeddings": embeddings,
                    "model": embedding_request.model,
                    "count": len(embeddings)
                }
                
            except EmbeddingModelNotFoundException as e:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=str(e)
                )
            except EmbeddingGenerationException as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=str(e)
                )
            except Exception as e:
                logger.error(f"Error al generar embeddings: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error al generar embeddings: {str(e)}"
                )
        
        @self.router.post("")
        async def search(request: dict):
            try:
                if "query" not in request:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="El campo 'query' es obligatorio"
                    )
                
                if "dataset_id" not in request:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="El campo 'dataset_id' es obligatorio"
                    )
                
                search_request = SearchRequest(
                    query=request["query"],
                    dataset_id=request["dataset_id"],
                    limit=request.get("limit", 10),
                    search_type=request.get("search_type", "semantic"),
                    embedding_model=request.get("embedding_model", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"),
                    hybrid_alpha=request.get("hybrid_alpha", 0.5),
                    additional_params=request.get("additional_params")
                )
                
                results = await self.search_service.search(
                    query=search_request.query,
                    dataset_id=search_request.dataset_id,
                    limit=search_request.limit,
                    search_type=search_request.search_type,
                    embedding_model=search_request.embedding_model,
                    hybrid_alpha=search_request.hybrid_alpha,
                    additional_params=search_request.additional_params
                )
                
                return {
                    "search_id": str(results.search_id),
                    "query": results.query,
                    "dataset_id": results.dataset_id,
                    "total_results": results.total_results,
                    "execution_time_ms": results.execution_time_ms,
                    "results": [
                        {
                            "id": result.id,
                            "text": result.text,
                            "score": result.score,
                            "metadata": result.metadata,
                            **result.data
                        }
                        for result in results.results
                    ]
                }
                
            except DatasetNotFoundException as e:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=str(e)
                )
            except EmptyQueryException as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )
            except InvalidSearchTypeException as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )
            except DataStorageConnectionException as e:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=str(e)
                )
            except SearchExecutionException as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=str(e)
                )
            except Exception as e:
                logger.error(f"Error al realizar búsqueda: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error al realizar búsqueda: {str(e)}"
                )
        
        @self.router.get("/models")
        async def list_models():
            """Lista todos los modelos de embedding disponibles"""
            try:
                models = await self.search_service.list_available_models()
                return {"models": models}
            except Exception as e:
                logger.error(f"Error al listar modelos: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error al listar modelos: {str(e)}"
                )
        
        @self.router.get("/models/{model_name}")
        async def get_model_info(model_name: str):
            """Obtiene información sobre un modelo de embedding"""
            try:
                model_info = await self.search_service.get_model_info(model_name)
                return model_info
            except EmbeddingModelNotFoundException as e:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=str(e)
                )
            except Exception as e:
                logger.error(f"Error al obtener información del modelo: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error al obtener información del modelo: {str(e)}"
                ) 