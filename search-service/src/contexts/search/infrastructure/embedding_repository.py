import os
import logging
from typing import List, Dict, Any, Optional
import numpy as np

from ..domain.repositories import EmbeddingRepository
from ..domain.value_objects import EmbeddingRequest
from ..domain.exceptions import EmbeddingModelNotFoundException, EmbeddingGenerationException

from ....infrastructure.embedding import EmbeddingStrategyFactory

logger = logging.getLogger(__name__)


class EmbeddingRepositoryImpl(EmbeddingRepository):
    
    def __init__(self):
        self.default_model = os.getenv("DEFAULT_EMBEDDING_MODEL", "sentence-transformer")
        self.default_model_params = {
            "model_name": os.getenv("DEFAULT_MODEL_NAME", "paraphrase-multilingual-MiniLM-L12-v2")
        }
        
        self.model_cache = {}
        
        logger.info(f"Repositorio de embeddings inicializado con modelo por defecto: {self.default_model}")
    
    async def generate_embeddings(self, request: EmbeddingRequest) -> np.ndarray:
        try:
            model_parts = request.model.split("/")
            if len(model_parts) > 1:
                strategy_name = "sentence-transformers"
                model_name = request.model
            else:
                strategy_name = request.model
                model_name = self.default_model_params.get("model_name")
            
            # Obtener o crear la estrategia
            strategy_key = f"{strategy_name}:{model_name}"
            if strategy_key not in self.model_cache:
                try:
                    strategy = EmbeddingStrategyFactory.get_strategy(
                        strategy_name,
                        model_name=model_name
                    )
                    self.model_cache[strategy_key] = strategy
                except Exception as e:
                    raise EmbeddingModelNotFoundException(request.model)
            
            strategy = self.model_cache[strategy_key]
            
            # Generar embeddings
            embeddings = strategy.generate_embeddings(
                request.texts,
                batch_size=request.batch_size,
                **request.additional_params
            )
            
            return embeddings
            
        except EmbeddingModelNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error al generar embeddings: {str(e)}")
            raise EmbeddingGenerationException(str(e), request.model)
    
    async def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """Obtiene información sobre un modelo de embedding"""
        try:
            # Determinar qué estrategia usar
            model_parts = model_name.split("/")
            if len(model_parts) > 1:
                strategy_name = "sentence-transformers"
                model_param = model_name
            else:
                strategy_name = model_name
                model_param = self.default_model_params.get("model_name")
            
            # Obtener o crear la estrategia
            strategy_key = f"{strategy_name}:{model_param}"
            if strategy_key not in self.model_cache:
                try:
                    strategy = EmbeddingStrategyFactory.get_strategy(
                        strategy_name,
                        model_name=model_param
                    )
                    self.model_cache[strategy_key] = strategy
                except Exception as e:
                    raise EmbeddingModelNotFoundException(model_name)
            
            strategy = self.model_cache[strategy_key]
            
            # Obtener información del modelo
            return strategy.get_model_info()
            
        except EmbeddingModelNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error al obtener información del modelo: {str(e)}")
            raise EmbeddingGenerationException(str(e), model_name)
    
    async def list_available_models(self) -> List[Dict[str, Any]]:
        """Lista todos los modelos de embedding disponibles"""
        models = []
        
        # Listar estrategias disponibles
        strategies = EmbeddingStrategyFactory.list_available_strategies()
        
        # Modelos predefinidos
        predefined_models = {
            "sentence-transformer": [
                "all-MiniLM-L6-v2",
                "all-mpnet-base-v2",
                "paraphrase-multilingual-MiniLM-L12-v2"
            ],
            "bert": [
                "bert-base-uncased",
                "bert-large-uncased",
                "distilbert-base-uncased"
            ],
            "openai": [
                "text-embedding-ada-002",
                "text-embedding-3-small",
                "text-embedding-3-large"
            ]
        }
        
        # Agregar modelos predefinidos
        for strategy_name in strategies:
            if strategy_name in predefined_models:
                for model_name in predefined_models[strategy_name]:
                    try:
                        # Crear estrategia temporalmente para obtener información
                        strategy = EmbeddingStrategyFactory.get_strategy(
                            strategy_name,
                            model_name=model_name
                        )
                        
                        # Obtener información del modelo
                        model_info = strategy.get_model_info()
                        models.append(model_info)
                    except Exception as e:
                        raise Exception(f"No se pudo obtener información del modelo {model_name}: {str(e)}")
        
        return models 