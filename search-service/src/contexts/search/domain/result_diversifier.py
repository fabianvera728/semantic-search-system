from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
import logging
from dataclasses import dataclass

from .entities import SearchResult, EmbeddingCollection

logger = logging.getLogger(__name__)


@dataclass
class DiversificationConfig:
    """Configuración para la diversificación de resultados"""
    similarity_threshold: float = 0.85      # Umbral de similitud para considerar duplicados
    lambda_param: float = 0.7               # Parámetro λ para MMR (balance relevancia-diversidad)
    max_similar_results: int = 3            # Máximo de resultados similares permitidos
    enable_semantic_clustering: bool = True  # Habilitar clustering semántico


class ResultDiversifier(ABC):
    """Interfaz base para diversificación de resultados de búsqueda"""
    
    @abstractmethod
    def diversify_results(
        self,
        results: List[SearchResult],
        embedding_collection: EmbeddingCollection,
        limit: int,
        config: DiversificationConfig
    ) -> List[SearchResult]:
        """Diversifica los resultados para reducir redundancia"""
        pass


class MMRDiversifier(ResultDiversifier):
    """Diversificador basado en Maximal Marginal Relevance (MMR)"""
    
    def __init__(self):
        """Inicializa el diversificador MMR"""
        self.embedding_cache = {}
        logger.info("Diversificador MMR inicializado")
    
    def diversify_results(
        self,
        results: List[SearchResult],
        embedding_collection: EmbeddingCollection,
        limit: int,
        config: DiversificationConfig
    ) -> List[SearchResult]:
        """
        Aplica diversificación usando Maximal Marginal Relevance (MMR)
        
        Args:
            results: Lista de resultados de búsqueda ordenados por relevancia
            embedding_collection: Colección de embeddings
            limit: Número máximo de resultados a retornar
            config: Configuración de diversificación
            
        Returns:
            List[SearchResult]: Resultados diversificados
        """
        
        if len(results) <= limit:
            logger.debug(f"Número de resultados ({len(results)}) menor o igual al límite ({limit})")
            return results
        
        logger.info(f"Diversificando {len(results)} resultados para obtener {limit} finales")
        
        # Seleccionar el mejor resultado como punto de partida
        selected_results = [results[0]]
        remaining_results = results[1:]
        
        # Construir cache de embeddings para eficiencia
        self._build_embedding_cache(results, embedding_collection)
        
        # Aplicar algoritmo MMR iterativamente
        while len(selected_results) < limit and remaining_results:
            best_candidate, best_mmr_score = self._find_best_mmr_candidate(
                remaining_results, selected_results, config.lambda_param
            )
            
            if best_candidate:
                selected_results.append(best_candidate)
                remaining_results.remove(best_candidate)
                
                logger.debug(f"Seleccionado resultado con MMR score: {best_mmr_score:.3f}")
            else:
                logger.warning("No se encontró candidato válido para MMR")
                break
        
        logger.info(f"Diversificación completada: {len(selected_results)} resultados seleccionados")
        return selected_results
    
    def _build_embedding_cache(
        self, 
        results: List[SearchResult], 
        embedding_collection: EmbeddingCollection
    ) -> None:
        """Construye cache de embeddings para acceso eficiente"""
        
        self.embedding_cache.clear()
        
        for result in results:
            embedding = self._get_embedding_by_id(result.id, embedding_collection)
            if embedding is not None:
                self.embedding_cache[result.id] = embedding
        
        logger.debug(f"Cache de embeddings construido con {len(self.embedding_cache)} entradas")
    
    def _find_best_mmr_candidate(
        self,
        candidates: List[SearchResult],
        selected_results: List[SearchResult],
        lambda_param: float
    ) -> Tuple[Optional[SearchResult], float]:
        """
        Encuentra el mejor candidato según el criterio MMR
        
        Args:
            candidates: Lista de candidatos
            selected_results: Resultados ya seleccionados
            lambda_param: Parámetro λ para balance relevancia-diversidad
            
        Returns:
            Tuple[SearchResult, float]: Mejor candidato y su puntuación MMR
        """
        
        best_candidate = None
        best_mmr_score = -float('inf')
        
        for candidate in candidates:
            # Obtener puntuación de relevancia original
            relevance_score = candidate.score
            
            # Calcular máxima similitud con resultados ya seleccionados
            max_similarity = self._calculate_max_similarity_with_selected(
                candidate, selected_results
            )
            
            # Calcular puntuación MMR: λ * relevancia - (1-λ) * max_similitud
            mmr_score = lambda_param * relevance_score - (1 - lambda_param) * max_similarity
            
            if mmr_score > best_mmr_score:
                best_mmr_score = mmr_score
                best_candidate = candidate
        
        return best_candidate, best_mmr_score
    
    def _calculate_max_similarity_with_selected(
        self,
        candidate: SearchResult,
        selected_results: List[SearchResult]
    ) -> float:
        """
        Calcula la máxima similitud entre el candidato y los resultados seleccionados
        
        Args:
            candidate: Resultado candidato
            selected_results: Resultados ya seleccionados
            
        Returns:
            float: Máxima similitud encontrada
        """
        
        if not selected_results:
            return 0.0
        
        candidate_embedding = self.embedding_cache.get(candidate.id)
        if candidate_embedding is None:
            # Fallback a similitud textual si no hay embedding
            return self._calculate_textual_similarity(candidate, selected_results)
        
        max_similarity = 0.0
        
        for selected in selected_results:
            selected_embedding = self.embedding_cache.get(selected.id)
            
            if selected_embedding is not None:
                # Calcular similitud coseno
                similarity = self._cosine_similarity(candidate_embedding, selected_embedding)
                max_similarity = max(max_similarity, similarity)
        
        return max_similarity
    
    def _calculate_textual_similarity(
        self,
        candidate: SearchResult,
        selected_results: List[SearchResult]
    ) -> float:
        """Calcula similitud textual como fallback cuando no hay embeddings"""
        
        candidate_words = set(candidate.text.lower().split())
        max_similarity = 0.0
        
        for selected in selected_results:
            selected_words = set(selected.text.lower().split())
            
            # Calcular similitud Jaccard
            intersection = len(candidate_words.intersection(selected_words))
            union = len(candidate_words.union(selected_words))
            
            similarity = intersection / union if union > 0 else 0.0
            max_similarity = max(max_similarity, similarity)
        
        return max_similarity
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calcula similitud coseno entre dos vectores"""
        
        # Normalizar vectores
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        # Calcular similitud coseno
        similarity = np.dot(vec1, vec2) / (norm1 * norm2)
        
        # Convertir a rango [0, 1] desde [-1, 1]
        return (similarity + 1.0) / 2.0
    
    def _get_embedding_by_id(
        self, 
        result_id: str, 
        embedding_collection: EmbeddingCollection
    ) -> Optional[np.ndarray]:
        """Obtiene embedding por ID del resultado"""
        
        for embedding_vector in embedding_collection.embeddings:
            if embedding_vector.id == result_id:
                return embedding_vector.vector
        
        return None


class ClusterBasedDiversifier(ResultDiversifier):
    """Diversificador basado en clustering semántico"""
    
    def __init__(self, n_clusters: int = 5):
        """
        Inicializa el diversificador basado en clusters
        
        Args:
            n_clusters: Número de clusters a formar
        """
        self.n_clusters = n_clusters
        logger.info(f"Diversificador basado en clusters inicializado con {n_clusters} clusters")
    
    def diversify_results(
        self,
        results: List[SearchResult],
        embedding_collection: EmbeddingCollection,
        limit: int,
        config: DiversificationConfig
    ) -> List[SearchResult]:
        """
        Diversifica resultados usando clustering semántico
        
        Args:
            results: Lista de resultados
            embedding_collection: Colección de embeddings
            limit: Límite de resultados
            config: Configuración de diversificación
            
        Returns:
            List[SearchResult]: Resultados diversificados por clusters
        """
        
        if len(results) <= limit:
            return results
        
        try:
            from sklearn.cluster import KMeans
            
            # Extraer embeddings de los resultados
            embeddings_matrix = self._extract_embeddings_matrix(results, embedding_collection)
            
            if embeddings_matrix is None or embeddings_matrix.shape[0] == 0:
                logger.warning("No se pudieron extraer embeddings, usando diversificación textual")
                return self._textual_diversification(results, limit)
            
            # Aplicar clustering
            n_clusters = min(self.n_clusters, len(results), limit)
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(embeddings_matrix)
            
            # Seleccionar mejores resultados de cada cluster
            diversified_results = self._select_from_clusters(results, cluster_labels, limit)
            
            logger.info(f"Clustering completado: {len(diversified_results)} resultados de {n_clusters} clusters")
            return diversified_results
            
        except ImportError:
            logger.warning("sklearn no disponible, usando MMR como fallback")
            mmr_diversifier = MMRDiversifier()
            return mmr_diversifier.diversify_results(results, embedding_collection, limit, config)
        except Exception as e:
            logger.error(f"Error en clustering: {str(e)}, usando fallback")
            return results[:limit]
    
    def _extract_embeddings_matrix(
        self, 
        results: List[SearchResult], 
        embedding_collection: EmbeddingCollection
    ) -> Optional[np.ndarray]:
        """Extrae matriz de embeddings de los resultados"""
        
        embeddings_list = []
        
        for result in results:
            for embedding_vector in embedding_collection.embeddings:
                if embedding_vector.id == result.id:
                    embeddings_list.append(embedding_vector.vector)
                    break
        
        if not embeddings_list:
            return None
        
        return np.vstack(embeddings_list)
    
    def _select_from_clusters(
        self, 
        results: List[SearchResult], 
        cluster_labels: np.ndarray, 
        limit: int
    ) -> List[SearchResult]:
        """Selecciona los mejores resultados de cada cluster"""
        
        # Agrupar resultados por cluster
        clusters = {}
        for i, (result, label) in enumerate(zip(results, cluster_labels)):
            if label not in clusters:
                clusters[label] = []
            clusters[label].append((result, i))
        
        # Ordenar clusters por el mejor score de cada uno
        sorted_clusters = sorted(
            clusters.items(),
            key=lambda x: max(result.score for result, _ in x[1]),
            reverse=True
        )
        
        # Seleccionar resultados distribuyendo entre clusters
        selected_results = []
        cluster_index = 0
        
        while len(selected_results) < limit and sorted_clusters:
            cluster_label, cluster_results = sorted_clusters[cluster_index]
            
            # Ordenar resultados del cluster por score y tomar el mejor disponible
            cluster_results.sort(key=lambda x: x[0].score, reverse=True)
            
            for result, original_index in cluster_results:
                if result not in selected_results:
                    selected_results.append(result)
                    break
            
            # Remover cluster si está vacío
            if not any(result not in selected_results for result, _ in cluster_results):
                sorted_clusters.pop(cluster_index)
                cluster_index = cluster_index % len(sorted_clusters) if sorted_clusters else 0
            else:
                cluster_index = (cluster_index + 1) % len(sorted_clusters)
        
        return selected_results
    
    def _textual_diversification(self, results: List[SearchResult], limit: int) -> List[SearchResult]:
        """Diversificación textual simple como fallback"""
        
        selected = [results[0]]  # Seleccionar el mejor
        
        for candidate in results[1:]:
            if len(selected) >= limit:
                break
            
            # Verificar si es suficientemente diferente
            is_diverse = True
            candidate_words = set(candidate.text.lower().split())
            
            for selected_result in selected:
                selected_words = set(selected_result.text.lower().split())
                intersection = len(candidate_words.intersection(selected_words))
                union = len(candidate_words.union(selected_words))
                similarity = intersection / union if union > 0 else 0.0
                
                if similarity > 0.7:  # Umbral de similitud
                    is_diverse = False
                    break
            
            if is_diverse:
                selected.append(candidate)
        
        return selected 