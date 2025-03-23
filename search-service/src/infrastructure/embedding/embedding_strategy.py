from abc import ABC, abstractmethod
import numpy as np
from typing import List, Dict, Any, Optional, Type
import os
import logging

logger = logging.getLogger(__name__)


class EmbeddingStrategy(ABC):
    """Estrategia base para generar embeddings"""
    
    @abstractmethod
    def generate_embeddings(self, texts: List[str], **kwargs) -> np.ndarray:
        """Genera embeddings para una lista de textos"""
        pass
    
    @abstractmethod
    def get_dimension(self) -> int:
        """Devuelve la dimensión de los embeddings generados"""
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Devuelve información sobre el modelo"""
        pass
    
    @classmethod
    @abstractmethod
    def get_strategy_name(cls) -> str:
        """Devuelve el nombre de la estrategia"""
        pass


class SentenceTransformerStrategy(EmbeddingStrategy):
    """Estrategia para generar embeddings usando Sentence Transformers"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Inicializa la estrategia con un modelo de Sentence Transformers"""
        try:
            from sentence_transformers import SentenceTransformer
            self.model_name = model_name
            self.model = SentenceTransformer(model_name)
            logger.info(f"[✅] Modelo Sentence Transformer '{model_name}' cargado correctamente")
        except Exception as e:
            logger.error(f"[❌] Error al cargar el modelo Sentence Transformer '{model_name}': {str(e)}")
            raise
    
    def generate_embeddings(self, texts: List[str], **kwargs) -> np.ndarray:
        """Genera embeddings para una lista de textos"""
        batch_size = kwargs.get("batch_size", 32)
        show_progress_bar = kwargs.get("show_progress_bar", False)
        
        # Verificar si hay textos
        if not texts:
            return np.array([], dtype=np.float32)
        
        # Generar embeddings
        embeddings = self.model.encode(
            texts, 
            batch_size=batch_size, 
            show_progress_bar=show_progress_bar,
            convert_to_numpy=True
        )
        
        return embeddings
    
    def get_dimension(self) -> int:
        """Devuelve la dimensión de los embeddings generados"""
        return self.model.get_sentence_embedding_dimension()
    
    def get_model_info(self) -> Dict[str, Any]:
        """Devuelve información sobre el modelo"""
        return {
            "name": self.model_name,
            "type": "sentence-transformers",
            "dimension": self.get_dimension(),
            "description": "Modelo de Sentence Transformers para generar embeddings"
        }
    
    @classmethod
    def get_strategy_name(cls) -> str:
        """Devuelve el nombre de la estrategia"""
        return "sentence-transformers"


class UniversalSentenceEncoderStrategy(EmbeddingStrategy):
    """Estrategia para generar embeddings usando Universal Sentence Encoder"""
    
    def __init__(self, model_url: Optional[str] = None):
        """Inicializa la estrategia con el modelo Universal Sentence Encoder"""
        try:
            import tensorflow as tf
            import tensorflow_hub as hub
            
            # Usar URL por defecto si no se proporciona
            if model_url is None:
                model_url = "https://tfhub.dev/google/universal-sentence-encoder/4"
            
            self.model_url = model_url
            self.model = hub.load(model_url)
            logger.info(f"Modelo Universal Sentence Encoder cargado correctamente desde {model_url}")
            
            # Obtener dimensión del modelo
            sample_text = ["Sample text to get embedding dimension"]
            sample_embedding = self.model(sample_text)
            self.dimension = sample_embedding.shape[1]
            
        except Exception as e:
            logger.error(f"Error al cargar el modelo Universal Sentence Encoder: {str(e)}")
            raise
    
    def generate_embeddings(self, texts: List[str], **kwargs) -> np.ndarray:
        """Genera embeddings para una lista de textos"""
        # Verificar si hay textos
        if not texts:
            return np.array([], dtype=np.float32)
        
        # Generar embeddings
        embeddings = self.model(texts).numpy()
        
        return embeddings
    
    def get_dimension(self) -> int:
        """Devuelve la dimensión de los embeddings generados"""
        return self.dimension
    
    def get_model_info(self) -> Dict[str, Any]:
        """Devuelve información sobre el modelo"""
        return {
            "name": "universal-sentence-encoder",
            "type": "tensorflow-hub",
            "dimension": self.get_dimension(),
            "model_url": self.model_url,
            "description": "Modelo Universal Sentence Encoder para generar embeddings"
        }
    
    @classmethod
    def get_strategy_name(cls) -> str:
        """Devuelve el nombre de la estrategia"""
        return "universal-sentence-encoder"


class BertStrategy(EmbeddingStrategy):
    """Estrategia para generar embeddings usando BERT"""
    
    def __init__(self, model_name: str = "bert-base-uncased"):
        """Inicializa la estrategia con un modelo BERT"""
        try:
            from transformers import AutoTokenizer, AutoModel
            import torch
            
            self.model_name = model_name
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModel.from_pretrained(model_name)
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            self.model.to(self.device)
            
            logger.info(f"Modelo BERT '{model_name}' cargado correctamente en {self.device}")
            
            # Obtener dimensión del modelo
            self.dimension = self.model.config.hidden_size
            
        except Exception as e:
            logger.error(f"Error al cargar el modelo BERT '{model_name}': {str(e)}")
            raise
    
    def generate_embeddings(self, texts: List[str], **kwargs) -> np.ndarray:
        """Genera embeddings para una lista de textos"""
        import torch
        
        # Verificar si hay textos
        if not texts:
            return np.array([], dtype=np.float32)
        
        batch_size = kwargs.get("batch_size", 32)
        embeddings = []
        
        # Procesar por lotes
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i+batch_size]
            
            # Tokenizar
            encoded_input = self.tokenizer(
                batch_texts, 
                padding=True, 
                truncation=True, 
                return_tensors="pt"
            ).to(self.device)
            
            # Calcular embeddings
            with torch.no_grad():
                model_output = self.model(**encoded_input)
                
            # Usar la representación [CLS] como embedding de la oración
            sentence_embeddings = model_output.last_hidden_state[:, 0, :].cpu().numpy()
            embeddings.append(sentence_embeddings)
        
        # Concatenar todos los lotes
        all_embeddings = np.vstack(embeddings)
        
        return all_embeddings
    
    def get_dimension(self) -> int:
        """Devuelve la dimensión de los embeddings generados"""
        return self.dimension
    
    def get_model_info(self) -> Dict[str, Any]:
        """Devuelve información sobre el modelo"""
        return {
            "name": self.model_name,
            "type": "bert",
            "dimension": self.get_dimension(),
            "description": "Modelo BERT para generar embeddings"
        }
    
    @classmethod
    def get_strategy_name(cls) -> str:
        """Devuelve el nombre de la estrategia"""
        return "bert"


class OpenAIStrategy(EmbeddingStrategy):
    """Estrategia para generar embeddings usando OpenAI"""
    
    def __init__(self, model_name: str = "text-embedding-ada-002"):
        """Inicializa la estrategia con un modelo de OpenAI"""
        try:
            import openai
            
            # Configurar API key
            openai.api_key = os.getenv("OPENAI_API_KEY")
            if not openai.api_key:
                raise ValueError("OPENAI_API_KEY no está configurada en las variables de entorno")
            
            self.model_name = model_name
            self.client = openai.OpenAI()
            
            # Dimensiones conocidas para modelos de OpenAI
            self.dimensions = {
                "text-embedding-ada-002": 1536,
                "text-embedding-3-small": 1536,
                "text-embedding-3-large": 3072
            }
            
            self.dimension = self.dimensions.get(model_name, 1536)
            
            logger.info(f"Cliente OpenAI configurado para usar el modelo '{model_name}'")
            
        except Exception as e:
            logger.error(f"Error al configurar el cliente OpenAI: {str(e)}")
            raise
    
    def generate_embeddings(self, texts: List[str], **kwargs) -> np.ndarray:
        """Genera embeddings para una lista de textos"""
        # Verificar si hay textos
        if not texts:
            return np.array([], dtype=np.float32)
        
        embeddings = []
        
        # OpenAI tiene límites en el número de solicitudes por minuto,
        # así que procesamos los textos en lotes pequeños
        batch_size = min(kwargs.get("batch_size", 10), 10)
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i+batch_size]
            
            try:
                # Llamar a la API de OpenAI
                response = self.client.embeddings.create(
                    model=self.model_name,
                    input=batch_texts
                )
                
                # Extraer embeddings de la respuesta
                for embedding_data in response.data:
                    embeddings.append(embedding_data.embedding)
                
            except Exception as e:
                logger.error(f"Error al generar embeddings con OpenAI: {str(e)}")
                raise
        
        # Convertir a numpy array
        return np.array(embeddings, dtype=np.float32)
    
    def get_dimension(self) -> int:
        """Devuelve la dimensión de los embeddings generados"""
        return self.dimension
    
    def get_model_info(self) -> Dict[str, Any]:
        """Devuelve información sobre el modelo"""
        return {
            "name": self.model_name,
            "type": "openai",
            "dimension": self.get_dimension(),
            "description": "Modelo de OpenAI para generar embeddings"
        }
    
    @classmethod
    def get_strategy_name(cls) -> str:
        """Devuelve el nombre de la estrategia"""
        return "openai"


class EmbeddingStrategyFactory:
    """Fábrica para crear estrategias de embedding"""
    
    _strategies: Dict[str, Type[EmbeddingStrategy]] = {
        SentenceTransformerStrategy.get_strategy_name(): SentenceTransformerStrategy,
        UniversalSentenceEncoderStrategy.get_strategy_name(): UniversalSentenceEncoderStrategy,
        BertStrategy.get_strategy_name(): BertStrategy,
        OpenAIStrategy.get_strategy_name(): OpenAIStrategy
    }
    
    @classmethod
    def get_strategy(cls, strategy_name: str, **kwargs) -> EmbeddingStrategy:
        """Obtiene una estrategia de embedding por su nombre"""
        strategy_class = cls._strategies.get(strategy_name)
        
        if not strategy_class:
            available_strategies = ", ".join(cls._strategies.keys())
            raise ValueError(f"Estrategia de embedding '{strategy_name}' no encontrada. "
                            f"Estrategias disponibles: {available_strategies}")
        
        return strategy_class(**kwargs)
    
    @classmethod
    def list_available_strategies(cls) -> List[str]:
        """Lista todas las estrategias de embedding disponibles"""
        return list(cls._strategies.keys())
    
    @classmethod
    def register_strategy(cls, strategy_class: Type[EmbeddingStrategy]) -> None:
        """Registra una nueva estrategia de embedding"""
        strategy_name = strategy_class.get_strategy_name()
        cls._strategies[strategy_name] = strategy_class
        logger.info(f"Estrategia de embedding '{strategy_name}' registrada correctamente") 