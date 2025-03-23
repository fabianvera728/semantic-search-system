from typing import Dict, Type, List
import logging
from .embedding_strategy import (
    EmbeddingStrategy, 
    SentenceTransformerStrategy,
    UniversalSentenceEncoderStrategy,
    BertStrategy,
    OpenAIStrategy
)

logger = logging.getLogger(__name__)

class EmbeddingStrategyFactory:
    """Fábrica para crear estrategias de embedding"""
    
    _strategies: Dict[str, Type[EmbeddingStrategy]] = {
        "sentence-transformers": SentenceTransformerStrategy,
        "universal-sentence-encoder": UniversalSentenceEncoderStrategy,
        "bert": BertStrategy,
        "openai": OpenAIStrategy
    }
    
    # Alias para mantener compatibilidad con código existente
    _aliases = {
        "sentence-transformers": "sentence-transformers"
    }
    
    @classmethod
    def get_strategy(cls, strategy_name: str, **kwargs) -> EmbeddingStrategy:
        """Crea una estrategia de embedding según el nombre"""
        
        # Verificar si es un alias
        if strategy_name in cls._aliases:
            logger.warning(f"Uso de nombre obsoleto '{strategy_name}'. Se usará '{cls._aliases[strategy_name]}' en su lugar.")
            strategy_name = cls._aliases[strategy_name]
            
        if strategy_name not in cls._strategies:
            raise ValueError(f"Estrategia '{strategy_name}' no encontrada")
        
        strategy_class = cls._strategies[strategy_name]
        return strategy_class(**kwargs)
    
    @classmethod
    def list_available_strategies(cls) -> List[str]:
        """Lista todas las estrategias disponibles"""
        return list(cls._strategies.keys())
    
    @classmethod
    def register_strategy(cls, strategy_class: Type[EmbeddingStrategy]) -> None:
        """Registra una nueva estrategia"""
        strategy_name = strategy_class.get_strategy_name()
        cls._strategies[strategy_name] = strategy_class
        logger.info(f"Estrategia '{strategy_name}' registrada correctamente") 