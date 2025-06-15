import logging
import numpy as np
from typing import List, Dict, Any, Optional, Union, Tuple
from dataclasses import dataclass
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
import time
import threading
from collections import deque
import re
import unicodedata

from .embedding_strategy import EmbeddingStrategy

logger = logging.getLogger(__name__)


@dataclass
class BatchProcessingConfig:
    """Configuración para procesamiento por lotes"""
    max_batch_size: int = 64           # Tamaño máximo de lote
    min_batch_size: int = 8            # Tamaño mínimo de lote
    max_text_length: int = 512         # Longitud máxima de texto
    enable_parallel_processing: bool = True    # Habilitar procesamiento paralelo
    num_workers: int = 4               # Número de trabajadores paralelos
    batch_timeout_seconds: float = 5.0  # Timeout para formación de lotes
    enable_smart_batching: bool = True  # Habilitar agrupación inteligente


@dataclass
class TextProcessingConfig:
    """Configuración para preprocesamiento de texto"""
    normalize_unicode: bool = True     # Normalizar caracteres Unicode
    remove_extra_whitespace: bool = True  # Eliminar espacios extra
    preserve_case: bool = True         # Preservar mayúsculas/minúsculas
    handle_special_chars: bool = True  # Manejar caracteres especiales
    smart_truncation: bool = True      # Truncamiento inteligente
    min_text_length: int = 3          # Longitud mínima de texto


class BatchProcessor:
    """Procesador de lotes optimizado para embeddings"""
    
    def __init__(self, config: BatchProcessingConfig):
        """
        Inicializa el procesador de lotes
        
        Args:
            config: Configuración de procesamiento por lotes
        """
        self.config = config
        self.pending_batches: deque = deque()
        self.batch_lock = threading.Lock()
        self.executor = ThreadPoolExecutor(max_workers=config.num_workers) if config.enable_parallel_processing else None
        
        logger.info(f"Procesador de lotes inicializado - Max batch: {config.max_batch_size}, "
                   f"Workers: {config.num_workers}, Parallel: {config.enable_parallel_processing}")
    
    def process_batches(
        self, 
        texts: List[str], 
        batch_size: int,
        strategy_func: callable
    ) -> np.ndarray:
        """
        Procesa textos en lotes optimizados
        
        Args:
            texts: Lista de textos a procesar
            batch_size: Tamaño de lote deseado
            strategy_func: Función de estrategia para procesar cada lote
            
        Returns:
            np.ndarray: Embeddings generados
        """
        
        if not texts:
            return np.array([], dtype=np.float32)
        
        # Ajustar tamaño de lote según configuración
        optimal_batch_size = self._calculate_optimal_batch_size(len(texts), batch_size)
        
        # Crear lotes
        batches = self._create_batches(texts, optimal_batch_size)
        
        # Procesar lotes
        if self.config.enable_parallel_processing and len(batches) > 1:
            embeddings = self._process_batches_parallel(batches, strategy_func)
        else:
            embeddings = self._process_batches_sequential(batches, strategy_func)
        
        return embeddings
    
    def _calculate_optimal_batch_size(self, total_texts: int, requested_batch_size: int) -> int:
        """Calcula el tamaño óptimo de lote"""
        
        # Respetar límites configurados
        optimal_size = max(self.config.min_batch_size, 
                          min(self.config.max_batch_size, requested_batch_size))
        
        # Ajustar para evitar lotes muy pequeños al final
        if total_texts > optimal_size:
            remainder = total_texts % optimal_size
            if remainder > 0 and remainder < self.config.min_batch_size:
                # Redistribuir para evitar lote final muy pequeño
                optimal_size = max(self.config.min_batch_size, 
                                 total_texts // (total_texts // optimal_size + 1))
        
        return optimal_size
    
    def _create_batches(self, texts: List[str], batch_size: int) -> List[List[str]]:
        """Crea lotes de textos"""
        
        if self.config.enable_smart_batching:
            return self._create_smart_batches(texts, batch_size)
        else:
            return [texts[i:i + batch_size] for i in range(0, len(texts), batch_size)]
    
    def _create_smart_batches(self, texts: List[str], batch_size: int) -> List[List[str]]:
        """Crea lotes inteligentes agrupando textos similares en longitud"""
        
        # Ordenar textos por longitud para mejor eficiencia
        text_length_pairs = [(text, len(text)) for text in texts]
        text_length_pairs.sort(key=lambda x: x[1])
        
        batches = []
        current_batch = []
        
        for text, length in text_length_pairs:
            current_batch.append(text)
            
            if len(current_batch) >= batch_size:
                batches.append(current_batch)
                current_batch = []
        
        # Agregar lote final si no está vacío
        if current_batch:
            batches.append(current_batch)
        
        return batches
    
    def _process_batches_parallel(self, batches: List[List[str]], strategy_func: callable) -> np.ndarray:
        """Procesa lotes en paralelo"""
        
        futures = []
        for batch in batches:
            future = self.executor.submit(strategy_func, batch)
            futures.append(future)
        
        # Recopilar resultados
        batch_embeddings = []
        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result()
                batch_embeddings.append(result)
            except Exception as e:
                logger.error(f"Error procesando lote: {str(e)}")
                raise
        
        # Concatenar todos los embeddings
        if batch_embeddings:
            return np.vstack(batch_embeddings)
        else:
            return np.array([], dtype=np.float32)
    
    def _process_batches_sequential(self, batches: List[List[str]], strategy_func: callable) -> np.ndarray:
        """Procesa lotes secuencialmente"""
        
        batch_embeddings = []
        for batch in batches:
            try:
                result = strategy_func(batch)
                batch_embeddings.append(result)
            except Exception as e:
                logger.error(f"Error procesando lote: {str(e)}")
                raise
        
        # Concatenar todos los embeddings
        if batch_embeddings:
            return np.vstack(batch_embeddings)
        else:
            return np.array([], dtype=np.float32)
    
    def shutdown(self):
        """Cierra el procesador de lotes"""
        if self.executor:
            self.executor.shutdown(wait=True)


class TextPreprocessor:
    """Preprocesador de texto optimizado"""
    
    def __init__(self, config: TextProcessingConfig):
        """
        Inicializa el preprocesador
        
        Args:
            config: Configuración de preprocesamiento
        """
        self.config = config
        self.compiled_patterns = self._compile_regex_patterns()
        
        logger.info(f"Preprocesador de texto inicializado - Normalización: {config.normalize_unicode}, "
                   f"Truncamiento inteligente: {config.smart_truncation}")
    
    def _compile_regex_patterns(self) -> Dict[str, re.Pattern]:
        """Compila patrones regex para mejor rendimiento"""
        
        patterns = {}
        
        if self.config.remove_extra_whitespace:
            patterns['whitespace'] = re.compile(r'\s+')
        
        if self.config.handle_special_chars:
            patterns['special_chars'] = re.compile(r'[^\w\s\-.,!?;:()\[\]{}"\']', re.UNICODE)
        
        return patterns
    
    def preprocess_texts(self, texts: List[str]) -> List[str]:
        """
        Preprocesa lista de textos
        
        Args:
            texts: Lista de textos a procesar
            
        Returns:
            List[str]: Textos preprocesados
        """
        
        processed_texts = []
        
        for text in texts:
            processed_text = self._preprocess_single_text(text)
            processed_texts.append(processed_text)
        
        return processed_texts
    
    def _preprocess_single_text(self, text: str) -> str:
        """Preprocesa un solo texto"""
        
        if not text or not text.strip():
            return ""
        
        processed = text
        
        # 1. Normalización Unicode
        if self.config.normalize_unicode:
            processed = self._normalize_unicode(processed)
        
        # 2. Eliminar espacios extra
        if self.config.remove_extra_whitespace:
            processed = self.compiled_patterns['whitespace'].sub(' ', processed)
        
        # 3. Manejar caracteres especiales
        if self.config.handle_special_chars:
            processed = self._handle_special_characters(processed)
        
        # 4. Truncamiento inteligente
        if self.config.smart_truncation and len(processed) > self.config.max_text_length:
            processed = self._smart_truncate(processed, self.config.max_text_length)
        
        # 5. Verificar longitud mínima
        processed = processed.strip()
        if len(processed) < self.config.min_text_length:
            return ""
        
        return processed
    
    def _normalize_unicode(self, text: str) -> str:
        """Normaliza caracteres Unicode"""
        
        # Usar normalización NFKC para mejor compatibilidad
        normalized = unicodedata.normalize('NFKC', text)
        return normalized
    
    def _handle_special_characters(self, text: str) -> str:
        """Maneja caracteres especiales preservando estructura"""
        
        # Preservar algunos caracteres especiales importantes
        # pero eliminar otros que pueden causar problemas
        
        # Reemplazar caracteres problemáticos con espacios
        cleaned = self.compiled_patterns['special_chars'].sub(' ', text)
        
        # Normalizar espacios múltiples
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        return cleaned
    
    def _smart_truncate(self, text: str, max_length: int) -> str:
        """Trunca texto de forma inteligente preservando estructura"""
        
        if len(text) <= max_length:
            return text
        
        # Estrategia 1: Truncar en límite de oración
        sentences = re.split(r'[.!?]+', text)
        if len(sentences) > 1:
            result = ""
            for sentence in sentences:
                if len(result + sentence) <= max_length:
                    result += sentence + ". "
                else:
                    break
            
            if len(result.strip()) >= max_length * 0.7:  # Al menos 70% del límite
                return result.strip()
        
        # Estrategia 2: Truncar en límite de palabra
        words = text.split()
        if len(words) > 1:
            result = ""
            for word in words:
                if len(result + " " + word) <= max_length:
                    result += " " + word if result else word
                else:
                    break
            
            if len(result) >= max_length * 0.8:  # Al menos 80% del límite
                return result
        
        # Estrategia 3: Truncar con elipsis
        return text[:max_length - 3] + "..."


class OptimizedEmbeddingStrategy(EmbeddingStrategy):
    """Estrategia optimizada para generación de embeddings"""
    
    def __init__(
        self, 
        base_strategy: EmbeddingStrategy,
        batch_config: Optional[BatchProcessingConfig] = None,
        text_config: Optional[TextProcessingConfig] = None
    ):
        """
        Inicializa la estrategia optimizada
        
        Args:
            base_strategy: Estrategia base de embeddings
            batch_config: Configuración de procesamiento por lotes
            text_config: Configuración de preprocesamiento de texto
        """
        self.base_strategy = base_strategy
        self.batch_config = batch_config or BatchProcessingConfig()
        self.text_config = text_config or TextProcessingConfig()
        
        self.batch_processor = BatchProcessor(self.batch_config)
        self.text_preprocessor = TextPreprocessor(self.text_config)
        
        # Métricas de rendimiento
        self.processing_stats = {
            'total_requests': 0,
            'total_texts_processed': 0,
            'total_processing_time': 0.0,
            'cache_hits': 0,
            'preprocessing_time': 0.0,
            'embedding_generation_time': 0.0
        }
        
        logger.info("Estrategia de embeddings optimizada inicializada")
    
    def generate_embeddings(self, texts: List[str], **kwargs) -> np.ndarray:
        """
        Genera embeddings de forma optimizada
        
        Args:
            texts: Lista de textos
            **kwargs: Argumentos adicionales
            
        Returns:
            np.ndarray: Embeddings generados
        """
        
        start_time = time.time()
        self.processing_stats['total_requests'] += 1
        self.processing_stats['total_texts_processed'] += len(texts)
        
        try:
            # 1. Preprocesamiento optimizado
            preprocessing_start = time.time()
            processed_texts = self.text_preprocessor.preprocess_texts(texts)
            
            # Filtrar textos vacíos
            valid_texts = [text for text in processed_texts if text]
            
            if not valid_texts:
                logger.warning("No hay textos válidos después del preprocesamiento")
                return np.array([], dtype=np.float32)
            
            preprocessing_time = time.time() - preprocessing_start
            self.processing_stats['preprocessing_time'] += preprocessing_time
            
            # 2. Generación de embeddings por lotes
            embedding_start = time.time()
            batch_size = kwargs.get('batch_size', self.batch_config.max_batch_size)
            
            # Función para procesar lote individual
            def process_single_batch(batch_texts):
                return self.base_strategy.generate_embeddings(batch_texts, **kwargs)
            
            # Procesar en lotes optimizados
            embeddings = self.batch_processor.process_batches(
                valid_texts, batch_size, process_single_batch
            )
            
            embedding_time = time.time() - embedding_start
            self.processing_stats['embedding_generation_time'] += embedding_time
            
            # 3. Post-procesamiento (si es necesario)
            if kwargs.get('normalize_embeddings', False):
                embeddings = self._normalize_embeddings(embeddings)
            
            total_time = time.time() - start_time
            self.processing_stats['total_processing_time'] += total_time
            
            logger.debug(f"Embeddings generados - Textos: {len(valid_texts)}, "
                        f"Tiempo total: {total_time:.3f}s, "
                        f"Preprocesamiento: {preprocessing_time:.3f}s, "
                        f"Generación: {embedding_time:.3f}s")
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generando embeddings optimizados: {str(e)}")
            raise
    
    def _normalize_embeddings(self, embeddings: np.ndarray) -> np.ndarray:
        """Normaliza embeddings de forma controlada"""
        
        if embeddings.size == 0:
            return embeddings
        
        # Normalización L2 por fila
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        
        # Evitar división por cero
        safe_norms = np.where(norms > 1e-8, norms, 1.0)
        
        normalized = embeddings / safe_norms
        
        return normalized
    
    def get_dimension(self) -> int:
        """Devuelve la dimensión de los embeddings"""
        return self.base_strategy.get_dimension()
    
    def get_model_info(self) -> Dict[str, Any]:
        """Devuelve información sobre el modelo"""
        base_info = self.base_strategy.get_model_info()
        
        # Agregar información de optimización
        base_info.update({
            'optimized': True,
            'batch_processing': True,
            'max_batch_size': self.batch_config.max_batch_size,
            'parallel_processing': self.batch_config.enable_parallel_processing,
            'text_preprocessing': True,
            'smart_truncation': self.text_config.smart_truncation,
            'processing_stats': self.get_processing_stats()
        })
        
        return base_info
    
    @classmethod
    def get_strategy_name(cls) -> str:
        """Devuelve el nombre de la estrategia"""
        return "optimized-embedding"
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de procesamiento"""
        
        stats = self.processing_stats.copy()
        
        # Calcular métricas derivadas
        if stats['total_requests'] > 0:
            stats['avg_texts_per_request'] = stats['total_texts_processed'] / stats['total_requests']
            stats['avg_processing_time_per_request'] = stats['total_processing_time'] / stats['total_requests']
        
        if stats['total_texts_processed'] > 0:
            stats['avg_processing_time_per_text'] = stats['total_processing_time'] / stats['total_texts_processed']
            stats['avg_preprocessing_time_per_text'] = stats['preprocessing_time'] / stats['total_texts_processed']
            stats['avg_embedding_time_per_text'] = stats['embedding_generation_time'] / stats['total_texts_processed']
        
        # Calcular eficiencia
        if stats['total_processing_time'] > 0:
            stats['preprocessing_efficiency'] = (stats['preprocessing_time'] / stats['total_processing_time']) * 100
            stats['embedding_efficiency'] = (stats['embedding_generation_time'] / stats['total_processing_time']) * 100
        
        return stats
    
    def reset_stats(self) -> None:
        """Reinicia las estadísticas de procesamiento"""
        
        self.processing_stats = {
            'total_requests': 0,
            'total_texts_processed': 0,
            'total_processing_time': 0.0,
            'cache_hits': 0,
            'preprocessing_time': 0.0,
            'embedding_generation_time': 0.0
        }
        
        logger.info("Estadísticas de procesamiento reiniciadas")
    
    def shutdown(self) -> None:
        """Cierra recursos de la estrategia optimizada"""
        
        self.batch_processor.shutdown()
        logger.info("Estrategia de embeddings optimizada cerrada") 