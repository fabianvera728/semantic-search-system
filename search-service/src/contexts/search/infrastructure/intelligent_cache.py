import time
import hashlib
import logging
from typing import Dict, Optional, List, Tuple, Any
from dataclasses import dataclass, field
from collections import OrderedDict
from threading import RLock
import json

from ..domain.entities import SearchResults, SearchResult

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Entrada individual del caché"""
    key: str
    value: SearchResults
    timestamp: float
    access_count: int = 0
    last_access: float = field(default_factory=time.time)
    similarity_score: float = 0.0  # Para consultas similares


@dataclass
class CacheConfig:
    """Configuración del sistema de caché"""
    max_size: int = 10000                    # Tamaño máximo del caché
    ttl_seconds: int = 3600                  # Time to live en segundos
    query_similarity_threshold: float = 0.85  # Umbral para consultas similares
    enable_similarity_search: bool = True     # Habilitar búsqueda por similitud
    cleanup_interval: int = 300              # Intervalo de limpieza en segundos
    max_memory_mb: int = 500                 # Límite de memoria en MB


class IntelligentCache:
    """Sistema de caché inteligente para búsquedas semánticas"""
    
    def __init__(self, config: CacheConfig):
        """
        Inicializa el caché inteligente
        
        Args:
            config: Configuración del caché
        """
        self.config = config
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.query_index: Dict[str, List[str]] = {}  # Índice de consultas para búsqueda rápida
        self.access_lock = RLock()
        self.last_cleanup = time.time()
        
        logger.info(f"Caché inteligente inicializado - Max size: {config.max_size}, "
                   f"TTL: {config.ttl_seconds}s, Similarity threshold: {config.query_similarity_threshold}")
    
    def get(self, query: str, dataset_id: str, search_config: Dict[str, Any]) -> Optional[SearchResults]:
        """
        Obtiene resultado del caché considerando similitud de consultas
        
        Args:
            query: Consulta de búsqueda
            dataset_id: ID del dataset
            search_config: Configuración de búsqueda
            
        Returns:
            SearchResults si existe en caché, None en caso contrario
        """
        
        with self.access_lock:
            # Generar clave de caché
            cache_key = self._generate_cache_key(query, dataset_id, search_config)
            
            # Buscar coincidencia exacta
            exact_match = self._get_exact_match(cache_key)
            if exact_match:
                logger.debug(f"Cache hit exacto para consulta: '{query[:50]}...'")
                return exact_match
            
            # Buscar consultas similares si está habilitado
            if self.config.enable_similarity_search:
                similar_result = self._find_similar_query_result(query, dataset_id, search_config)
                if similar_result:
                    logger.debug(f"Cache hit similar para consulta: '{query[:50]}...'")
                    return similar_result
            
            logger.debug(f"Cache miss para consulta: '{query[:50]}...'")
            return None
    
    def put(self, query: str, dataset_id: str, search_config: Dict[str, Any], results: SearchResults) -> None:
        """
        Almacena resultados en el caché
        
        Args:
            query: Consulta de búsqueda
            dataset_id: ID del dataset
            search_config: Configuración de búsqueda
            results: Resultados a almacenar
        """
        
        with self.access_lock:
            cache_key = self._generate_cache_key(query, dataset_id, search_config)
            
            # Crear entrada de caché
            entry = CacheEntry(
                key=cache_key,
                value=results,
                timestamp=time.time()
            )
            
            # Almacenar en caché
            self.cache[cache_key] = entry
            
            # Actualizar índice de consultas
            self._update_query_index(query, cache_key)
            
            # Verificar límites y limpiar si es necesario
            self._enforce_cache_limits()
            
            logger.debug(f"Resultado almacenado en caché para: '{query[:50]}...'")
    
    def _get_exact_match(self, cache_key: str) -> Optional[SearchResults]:
        """Obtiene coincidencia exacta del caché"""
        
        entry = self.cache.get(cache_key)
        if entry and self._is_cache_valid(entry):
            # Actualizar estadísticas de acceso
            entry.access_count += 1
            entry.last_access = time.time()
            
            # Mover al final (LRU)
            self.cache.move_to_end(cache_key)
            
            return entry.value
        elif entry:
            # Entrada expirada, remover
            del self.cache[cache_key]
            self._remove_from_query_index(cache_key)
        
        return None
    
    def _find_similar_query_result(
        self, 
        query: str, 
        dataset_id: str, 
        search_config: Dict[str, Any]
    ) -> Optional[SearchResults]:
        """Busca resultados de consultas similares en el caché"""
        
        query_words = set(self._normalize_query(query).split())
        best_match_key = None
        best_similarity = 0.0
        
        # Buscar en índice de consultas
        for indexed_query, cache_keys in self.query_index.items():
            indexed_words = set(indexed_query.split())
            
            # Calcular similitud Jaccard
            similarity = self._calculate_jaccard_similarity(query_words, indexed_words)
            
            if similarity >= self.config.query_similarity_threshold and similarity > best_similarity:
                # Verificar que al menos una clave es válida para este dataset
                for cache_key in cache_keys:
                    if cache_key in self.cache and dataset_id in cache_key:
                        entry = self.cache[cache_key]
                        if self._is_cache_valid(entry):
                            best_similarity = similarity
                            best_match_key = cache_key
                            break
        
        if best_match_key:
            entry = self.cache[best_match_key]
            entry.access_count += 1
            entry.last_access = time.time()
            entry.similarity_score = best_similarity
            
            # Mover al final (LRU)
            self.cache.move_to_end(best_match_key)
            
            return entry.value
        
        return None
    
    def _generate_cache_key(self, query: str, dataset_id: str, search_config: Dict[str, Any]) -> str:
        """Genera clave única para el caché"""
        
        # Normalizar consulta
        normalized_query = self._normalize_query(query)
        
        # Crear objeto de configuración relevante para caché
        cache_relevant_config = {
            'search_type': search_config.get('search_type', 'semantic'),
            'embedding_model': search_config.get('embedding_model', ''),
            'limit': search_config.get('limit', 10),
            'hybrid_alpha': search_config.get('hybrid_alpha', 0.5)
        }
        
        # Crear string para hash
        key_string = f"{normalized_query}|{dataset_id}|{json.dumps(cache_relevant_config, sort_keys=True)}"
        
        # Generar hash SHA-256
        return hashlib.sha256(key_string.encode('utf-8')).hexdigest()
    
    def _normalize_query(self, query: str) -> str:
        """Normaliza consulta para búsqueda consistente"""
        
        # Convertir a minúsculas y eliminar espacios extra
        normalized = ' '.join(query.lower().strip().split())
        
        # Remover caracteres especiales pero mantener acentos
        import re
        normalized = re.sub(r'[^\w\sáéíóúñü]', '', normalized)
        
        return normalized
    
    def _calculate_jaccard_similarity(self, set1: set, set2: set) -> float:
        """Calcula similitud Jaccard entre dos conjuntos"""
        
        if not set1 and not set2:
            return 1.0
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0
    
    def _update_query_index(self, query: str, cache_key: str) -> None:
        """Actualiza el índice de consultas"""
        
        normalized_query = self._normalize_query(query)
        
        if normalized_query not in self.query_index:
            self.query_index[normalized_query] = []
        
        if cache_key not in self.query_index[normalized_query]:
            self.query_index[normalized_query].append(cache_key)
    
    def _remove_from_query_index(self, cache_key: str) -> None:
        """Remueve clave del índice de consultas"""
        
        for query, keys in list(self.query_index.items()):
            if cache_key in keys:
                keys.remove(cache_key)
                if not keys:  # Remover consulta si no tiene claves
                    del self.query_index[query]
    
    def _is_cache_valid(self, entry: CacheEntry) -> bool:
        """Verifica si una entrada del caché es válida"""
        
        current_time = time.time()
        return (current_time - entry.timestamp) < self.config.ttl_seconds
    
    def _enforce_cache_limits(self) -> None:
        """Enforza límites de tamaño y memoria del caché"""
        
        # Limpieza periódica
        current_time = time.time()
        if (current_time - self.last_cleanup) > self.config.cleanup_interval:
            self._cleanup_expired_entries()
            self.last_cleanup = current_time
        
        # Enforza límite de tamaño
        while len(self.cache) > self.config.max_size:
            # Remover entrada menos reciente (LRU)
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
            self._remove_from_query_index(oldest_key)
            logger.debug(f"Entrada removida por límite de tamaño: {oldest_key[:32]}...")
    
    def _cleanup_expired_entries(self) -> None:
        """Limpia entradas expiradas del caché"""
        
        current_time = time.time()
        expired_keys = []
        
        for key, entry in self.cache.items():
            if not self._is_cache_valid(entry):
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.cache[key]
            self._remove_from_query_index(key)
        
        if expired_keys:
            logger.info(f"Limpieza completada: {len(expired_keys)} entradas expiradas removidas")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del caché"""
        
        total_entries = len(self.cache)
        total_access_count = sum(entry.access_count for entry in self.cache.values())
        
        if total_entries > 0:
            avg_access = total_access_count / total_entries
            most_accessed = max(self.cache.values(), key=lambda e: e.access_count)
        else:
            avg_access = 0
            most_accessed = None
        
        return {
            'total_entries': total_entries,
            'max_size': self.config.max_size,
            'total_accesses': total_access_count,
            'average_accesses_per_entry': avg_access,
            'query_index_size': len(self.query_index),
            'most_accessed_query': most_accessed.key[:50] + '...' if most_accessed else None,
            'most_accessed_count': most_accessed.access_count if most_accessed else 0,
            'cache_utilization': (total_entries / self.config.max_size) * 100
        }
    
    def clear_cache(self) -> None:
        """Limpia completamente el caché"""
        
        with self.access_lock:
            self.cache.clear()
            self.query_index.clear()
            logger.info("Caché completamente limpiado")
    
    def invalidate_dataset(self, dataset_id: str) -> int:
        """
        Invalida todas las entradas de caché para un dataset específico
        
        Args:
            dataset_id: ID del dataset a invalidar
            
        Returns:
            int: Número de entradas invalidadas
        """
        
        with self.access_lock:
            keys_to_remove = []
            
            for key in self.cache.keys():
                if dataset_id in key:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self.cache[key]
                self._remove_from_query_index(key)
            
            logger.info(f"Invalidadas {len(keys_to_remove)} entradas para dataset: {dataset_id}")
            return len(keys_to_remove)


class CacheManager:
    """Gestor del sistema de caché con múltiples instancias"""
    
    def __init__(self):
        """Inicializa el gestor de caché"""
        self.caches: Dict[str, IntelligentCache] = {}
        self.default_config = CacheConfig()
        
    def get_cache(self, cache_name: str = "default") -> IntelligentCache:
        """
        Obtiene instancia de caché por nombre
        
        Args:
            cache_name: Nombre del caché
            
        Returns:
            IntelligentCache: Instancia del caché
        """
        
        if cache_name not in self.caches:
            self.caches[cache_name] = IntelligentCache(self.default_config)
            logger.info(f"Nueva instancia de caché creada: {cache_name}")
        
        return self.caches[cache_name]
    
    def create_cache(self, cache_name: str, config: CacheConfig) -> IntelligentCache:
        """
        Crea nueva instancia de caché con configuración específica
        
        Args:
            cache_name: Nombre del caché
            config: Configuración del caché
            
        Returns:
            IntelligentCache: Nueva instancia del caché
        """
        
        self.caches[cache_name] = IntelligentCache(config)
        logger.info(f"Caché personalizado creado: {cache_name}")
        return self.caches[cache_name]
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Obtiene estadísticas de todos los cachés"""
        
        return {
            name: cache.get_cache_stats() 
            for name, cache in self.caches.items()
        }
    
    def clear_all_caches(self) -> None:
        """Limpia todos los cachés"""
        
        for cache in self.caches.values():
            cache.clear_cache()
        
        logger.info("Todos los cachés han sido limpiados") 