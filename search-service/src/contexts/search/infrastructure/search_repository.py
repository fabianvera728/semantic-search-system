import os
import logging
import time
import json
import httpx
import numpy as np
import faiss
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID

from ..domain.repositories import SearchRepository
from ..domain.entities import SearchResults, SearchResult, EmbeddingCollection, EmbeddingVector
from ..domain.value_objects import SearchRequest
from ..domain.exceptions import (
    DatasetNotFoundException, 
    SearchExecutionException, 
    InvalidSearchTypeException,
    DataStorageConnectionException,
    EmptyQueryException
)

# Importar las nuevas mejoras
from ..domain.scoring_strategy import BalancedScoringStrategy, ScoringStrategy
from ..domain.result_diversifier import MMRDiversifier, DiversificationConfig
from ..domain.search_quality_metrics import SearchQualityAnalyzer, PerformanceMonitor
from .intelligent_cache import IntelligentCache, CacheConfig, CacheManager

from .embedding_repository import EmbeddingRepositoryImpl
from ..domain.value_objects import EmbeddingRequest
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


class SearchRepositoryImpl(SearchRepository):
    
    def __init__(self, embedding_repository: Optional[EmbeddingRepositoryImpl] = None):
        self.embedding_repository = embedding_repository or EmbeddingRepositoryImpl()
        self.data_storage_url = os.getenv("DATA_STORAGE_URL", "http://data-storage:8003")
        self.embedding_service_url = os.getenv("EMBEDDING_SERVICE_URL", "http://embedding-service:8005")
        
        self.index_cache = {}
        self.embedding_cache = {}
        
        # Inicializar nuevos componentes mejorados
        self.scoring_strategy: ScoringStrategy = BalancedScoringStrategy()
        self.result_diversifier = MMRDiversifier()
        self.diversification_config = DiversificationConfig()
        self.quality_analyzer = SearchQualityAnalyzer()
        self.performance_monitor = PerformanceMonitor()
        
        # Inicializar sistema de caché inteligente
        cache_config = CacheConfig(
            max_size=int(os.getenv("CACHE_MAX_SIZE", "5000")),
            ttl_seconds=int(os.getenv("CACHE_TTL_SECONDS", "3600")),
            query_similarity_threshold=float(os.getenv("CACHE_SIMILARITY_THRESHOLD", "0.85"))
        )
        self.cache_manager = CacheManager()
        self.search_cache = self.cache_manager.create_cache("search_results", cache_config)
        
        logger.info(f"Repositorio de búsqueda mejorado inicializado con URL de almacenamiento: {self.data_storage_url}")
        logger.info(f"Mejoras habilitadas - Scoring balanceado: ✓, Diversificación MMR: ✓, Caché inteligente: ✓, Métricas de calidad: ✓")
    
    async def search(self, request: SearchRequest) -> SearchResults:
        start_time = time.time()
        cache_hit = False
        had_error = False
        
        try:
            if not request.query.text.strip():
                raise EmptyQueryException()
            
            # 1. Verificar caché inteligente primero
            search_config_dict = {
                'search_type': request.config.search_type,
                'embedding_model': request.config.embedding_model,
                'limit': request.config.limit,
                'hybrid_alpha': request.config.hybrid_alpha
            }
            
            cached_results = self.search_cache.get(
                request.query.text, 
                request.dataset_id.value, 
                search_config_dict
            )
            
            if cached_results:
                cache_hit = True
                execution_time = (time.time() - start_time) * 1000
                
                # Analizar calidad de resultados cacheados
                quality_report = self.quality_analyzer.analyze_search_quality(
                    cached_results, request.query.text, execution_time
                )
                
                # Registrar métricas de rendimiento
                self.performance_monitor.record_query(
                    execution_time, cache_hit, quality_report.quality_score, had_error
                )
                
                logger.debug(f"Cache hit para consulta: '{request.query.text[:50]}...' - "
                           f"Tiempo: {execution_time:.2f}ms, Calidad: {quality_report.quality_score:.3f}")
                
                return cached_results
            
            # 2. Realizar búsqueda completa si no hay caché
            dataset_id = request.dataset_id.value
            if dataset_id not in self.index_cache:
                await self._load_dataset(dataset_id)
            
            index = self.index_cache.get(dataset_id)
            embedding_collection = self.embedding_cache.get(dataset_id)
            
            if index is None or embedding_collection is None:
                raise DatasetNotFoundException(dataset_id)
            
            search_type = request.config.search_type
            initial_limit = min(request.config.limit * 3, 100)  # Obtener más resultados para diversificar
            
            # 3. Ejecutar búsqueda según el tipo
            if search_type == "semantic":
                initial_results = await self._enhanced_semantic_search(
                    request.query.text, 
                    index, 
                    embedding_collection, 
                    initial_limit,
                    request.config.embedding_model
                )
            elif search_type == "keyword":
                initial_results = await self._keyword_search(
                    request.query.text, 
                    embedding_collection, 
                    initial_limit
                )
            elif search_type == "hybrid":
                initial_results = await self._enhanced_hybrid_search(
                    request.query.text, 
                    index, 
                    embedding_collection, 
                    initial_limit,
                    request.config.embedding_model,
                    request.config.hybrid_alpha
                )
            else:
                raise InvalidSearchTypeException(search_type)
            
            # 4. Aplicar diversificación de resultados
            diversified_results = self.result_diversifier.diversify_results(
                initial_results,
                embedding_collection,
                request.config.limit,
                self.diversification_config
            )
            
            # 5. Enriquecer resultados con datos adicionales
            enriched_results = []
            for result in diversified_results:
                try:
                    row_data = await self._get_row_data(dataset_id, result.id)
                    result.data = row_data.get("data", {})
                    enriched_results.append(result)
                except Exception as e:
                    logger.warning(f"Error enriching result {result.id}: {str(e)}")
                    enriched_results.append(result)  # Incluir sin enrichment

            # 6. Crear objeto de resultados final
            execution_time = (time.time() - start_time) * 1000
            search_results = SearchResults(
                query=request.query.text,
                results=enriched_results,
                total_results=len(enriched_results),
                execution_time_ms=execution_time,
                dataset_id=dataset_id,
                search_id=request.search_id.value
            )
            
            # 7. Analizar calidad de resultados
            quality_report = self.quality_analyzer.analyze_search_quality(
                search_results, request.query.text, execution_time
            )
            
            # 8. Almacenar en caché si la calidad es suficiente
            if quality_report.quality_score >= 0.3:  # Umbral mínimo de calidad
                self.search_cache.put(
                    request.query.text,
                    request.dataset_id.value,
                    search_config_dict,
                    search_results
                )
            
            # 9. Registrar métricas de rendimiento
            self.performance_monitor.record_query(
                execution_time, cache_hit, quality_report.quality_score, had_error
            )
            
            # 10. Guardar resultados para análisis posterior
            await self.save_search_results(search_results)
            
            logger.info(f"Búsqueda completada - Query: '{request.query.text[:50]}...', "
                       f"Resultados: {len(enriched_results)}, "
                       f"Tiempo: {execution_time:.2f}ms, "
                       f"Calidad: {quality_report.quality_score:.3f}, "
                       f"Diversidad: {quality_report.diversity_score:.3f}")
            
            # Log recomendaciones si la calidad es baja
            if quality_report.quality_score < 0.6:
                for recommendation in quality_report.recommendations[:3]:  # Top 3
                    logger.info(f"Recomendación: {recommendation}")
            
            return search_results
            
        except (DatasetNotFoundException, EmptyQueryException, InvalidSearchTypeException):
            had_error = True
            # Registrar error en métricas
            execution_time = (time.time() - start_time) * 1000
            self.performance_monitor.record_query(execution_time, cache_hit, 0.0, had_error)
            raise
        except Exception as e:
            had_error = True
            execution_time = (time.time() - start_time) * 1000
            self.performance_monitor.record_query(execution_time, cache_hit, 0.0, had_error)
            logger.error(f"Error al realizar búsqueda: {str(e)}")
            raise SearchExecutionException(str(e), request.dataset_id.value)
    
    async def _get_row_data(self, dataset_id: str, row_id: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.data_storage_url}/datasets/{dataset_id}/rows/{row_id}",
                timeout=30.0
            )
            return response.json()

    async def _enhanced_semantic_search(
        self, 
        query: str, 
        index: faiss.Index, 
        embedding_collection: EmbeddingCollection, 
        limit: int,
        model_name: str
    ) -> List[SearchResult]:
        """Búsqueda semántica mejorada con estrategia de puntuación balanceada"""
        
        # Preprocesamiento de la consulta
        clean_query = query.strip()
        query_terms = set(clean_query.lower().split())
        
        # Generar embedding para la consulta
        embedding_request = EmbeddingRequest(
            texts=[clean_query],
            model=model_name
        )
        query_embedding = await self.embedding_repository.generate_embeddings(embedding_request)
        
        # Búsqueda en el índice FAISS
        search_limit = min(limit, len(embedding_collection.embeddings))
        distances, indices = index.search(query_embedding, search_limit)

        logger.debug(f"[📏] Metric type: {index.metric_type}")
        logger.debug(f"[🔍] Enhanced search for: {clean_query}")
        logger.debug(f"[🔍] Found {len(indices[0])} initial matches")
        from sklearn.feature_extraction.text import TfidfVectorizer

        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < 0 or idx >= len(embedding_collection.embeddings):
                continue
                
            embedding = embedding_collection.embeddings[idx]
            result_terms = set(embedding.text.lower().split())
            
            # Usar nueva estrategia de puntuación balanceada
            cosine_sim = 1.0 - float(distances[0][i])   # si usas L2 sobre vectores unitarios
            diversity_penalty = 0
            # o directamente: cosine_sim = float(similarities[0][i]) si tu índice devuelve similes

            # 2) Prepara vector TF–IDF para el term_score:
            #    (cachea tu vectorizer en el objeto para no regenerarlo por cada hit)

            if not hasattr(self, '_tfidf_vectorizer'):
                texts = embedding_collection.get_texts()
                self._tfidf_vectorizer = TfidfVectorizer().fit(texts + [clean_query])
            query_tfidf = self._tfidf_vectorizer.transform([clean_query])
            result_tfidf = self._tfidf_vectorizer.transform([embedding.text])
            tfidf_term_score = cosine_similarity(query_tfidf, result_tfidf)[0][0]

            # 3) Llamada reconfigurada a tu estrategia, pasando ahora `cosine_sim` y `tfidf_term_score`:
            final_score = self.scoring_strategy.calculate_score(
                semantic_score=cosine_sim,
                term_score=tfidf_term_score,
                result_length=len(embedding.text),
                query_length=len(clean_query),
                diversity_penalty=diversity_penalty
            )
            
            # Crear metadatos enriquecidos
            metadata = {
                **embedding.metadata,
                # "semantic_distance": semantic_distance,
                "query_terms_count": len(query_terms),
                "result_terms_count": len(result_terms),
                "term_overlap": len(query_terms.intersection(result_terms)),
                "text_length": len(embedding.text),
                "scoring_method": "balanced_strategy",
                "query": clean_query
            }
            
            # Crear resultado de búsqueda
            result = SearchResult(
                id=embedding.id,
                text=embedding.text,
                score=final_score,
                metadata=metadata
            )
            
            results.append(result)
        
        # Ordenar por puntuación descendente
        results.sort(key=lambda x: x.score, reverse=True)
        
        logger.debug(f"Enhanced semantic search completed - {len(results)} results")
        return results
    
    async def _enhanced_hybrid_search(
        self, 
        query: str, 
        index: faiss.Index, 
        embedding_collection: EmbeddingCollection, 
        limit: int,
        model_name: str,
        alpha: float = 0.5
    ) -> List[SearchResult]:
        """Búsqueda híbrida mejorada que combina búsqueda semántica y por palabras clave"""
        
        # Preprocesamiento de la consulta
        clean_query = query.strip()
        query_terms = set(clean_query.lower().split())
        
        # Obtener resultados de búsqueda semántica
        semantic_results = await self._enhanced_semantic_search(
            clean_query, 
            index, 
            embedding_collection, 
            limit * 2,  # Obtener más resultados para combinación
            model_name
        )
        
        # Obtener resultados de búsqueda por keywords
        keyword_results = await self._keyword_search(
            clean_query, 
            embedding_collection, 
            limit * 2
        )
        
        # Combinar resultados usando estrategia mejorada
        combined_results = {}
        
        # Procesar resultados semánticos
        for result in semantic_results:
            combined_results[result.id] = {
                "id": result.id,
                "text": result.text,
                "semantic_score": result.score,
                "keyword_score": 0.0,
                "metadata": result.metadata
            }
        
        # Procesar resultados por keywords
        for result in keyword_results:
            if result.id in combined_results:
                combined_results[result.id]["keyword_score"] = result.score
            else:
                combined_results[result.id] = {
                    "id": result.id,
                    "text": result.text,
                    "semantic_score": 0.0,
                    "keyword_score": result.score,
                    "metadata": result.metadata or {}
                }
        
        # Calcular puntuación combinada usando estrategia de scoring
        final_results = []
        for result_id, result_data in combined_results.items():
            # Combinar puntuaciones semántica y de palabras clave
            semantic_weight = alpha
            keyword_weight = 1 - alpha
            
            combined_score = (semantic_weight * result_data["semantic_score"] + 
                            keyword_weight * result_data["keyword_score"])
            
            # Crear metadatos enriquecidos
            metadata = {
                **result_data["metadata"],
                "semantic_score": result_data["semantic_score"],
                "keyword_score": result_data["keyword_score"],
                "combined_score": combined_score,
                "alpha_used": alpha,
                "search_method": "enhanced_hybrid",
                "query": clean_query
            }
            
            result = SearchResult(
                id=result_data["id"],
                text=result_data["text"],
                score=combined_score,
                metadata=metadata
            )
            final_results.append(result)
        
        # Ordenar por puntuación descendente
        final_results.sort(key=lambda x: x.score, reverse=True)
        
        logger.debug(f"Enhanced hybrid search completed - {len(final_results)} results")
        return final_results[:limit]
    
    async def _keyword_search(
        self, 
        query: str, 
        embedding_collection: EmbeddingCollection, 
        limit: int
    ) -> List[SearchResult]:

        
        texts = embedding_collection.get_texts()
        if not texts:
            return []
        
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(texts + [query])
        
        query_vector = tfidf_matrix[-1]
        document_vectors = tfidf_matrix[:-1]
        similarities = cosine_similarity(query_vector, document_vectors)[0]
        
        sorted_indices = np.argsort(similarities)[::-1][:limit]
        
        results = []
        for idx in sorted_indices:
            if similarities[idx] > 0:
                embedding = embedding_collection.embeddings[idx]
                result = SearchResult(
                    id=embedding.id,
                    text=embedding.text,
                    score=float(similarities[idx]),
                    metadata=embedding.metadata
                )
                results.append(result)
        
        return results
    
    async def _hybrid_search(
        self, 
        query: str, 
        index: faiss.Index, 
        embedding_collection: EmbeddingCollection, 
        limit: int,
        model_name: str,
        alpha: float = 0.5
    ) -> List[SearchResult]:
        # Preprocesamiento básico de la consulta
        query = query.strip()
        
        # Analizar la consulta para determinar si contiene términos específicos/nombres propios
        # que podrían beneficiarse de un enfoque más basado en keywords
        query_words = query.lower().split()
        
        # Obtener términos con mayúscula inicial (posibles nombres propios)
        proper_nouns = [word for word in query.split() if word and word[0].isupper()]
        
        # Heurística: si la consulta tiene palabras específicas o nombres propios
        # ajustamos el balance para dar más peso a coincidencias exactas
        dynamic_alpha = alpha
        if proper_nouns:
            # Si hay nombres propios, reducir el peso semántico
            dynamic_alpha = max(0.3, alpha - 0.2)
            logger.info(f"[🔍] Detected proper nouns in query, adjusting alpha to {dynamic_alpha}")
        
        # Duplicar limit para tener más candidatos
        search_limit = limit * 3
        
        # Obtener resultados de búsqueda semántica
        semantic_results = await self._semantic_search(
            query, 
            index, 
            embedding_collection, 
            search_limit,
            model_name
        )
        
        # Obtener resultados de búsqueda por keywords
        keyword_results = await self._keyword_search(
            query, 
            embedding_collection, 
            search_limit
        )
        
        # Combinar resultados
        combined_results = {}
        
        # Procesar resultados semánticos
        for result in semantic_results:
            combined_results[result.id] = {
                "id": result.id,
                "text": result.text,
                "semantic_score": result.score,
                "keyword_score": 0.0,
                "metadata": result.metadata,
                "match_count": 1  # Contador de cuántos métodos encontraron este resultado
            }
        
        # Procesar resultados por keywords
        for result in keyword_results:
            if result.id in combined_results:
                combined_results[result.id]["keyword_score"] = result.score
                combined_results[result.id]["match_count"] += 1
                # Combinar metadatos
                if "metadata" in result.__dict__ and result.metadata:
                    for key, value in result.metadata.items():
                        if key not in combined_results[result.id]["metadata"]:
                            combined_results[result.id]["metadata"][key] = value
            else:
                combined_results[result.id] = {
                    "id": result.id,
                    "text": result.text,
                    "semantic_score": 0.0,
                    "keyword_score": result.score,
                    "metadata": result.metadata or {},
                    "match_count": 1
                }
        
        # Calcular puntuación combinada con pesos ajustados y boosts
        for result_id, result_data in combined_results.items():
            semantic_score = result_data["semantic_score"]
            keyword_score = result_data["keyword_score"]
            
            # Factor de coincidencia: premiar resultados encontrados por ambos métodos
            match_boost = 1.0 + (result_data["match_count"] > 1) * 0.2
            
            # Factores para aumentar la relevancia
            result_text = result_data["text"].lower()
            query_terms = query.lower().split()
            
            # Calcular un boost basado en la presencia de términos de la consulta en el resultado
            term_match_count = sum(1 for term in query_terms if term in result_text)
            term_match_ratio = term_match_count / len(query_terms) if query_terms else 0
            term_boost = 1.0 + term_match_ratio * 0.2  # Aumentar hasta 20% si todos los términos están presentes
            
            # Calcular puntuación combinada con alpha dinámico y boosts
            combined_score = (dynamic_alpha * semantic_score + (1 - dynamic_alpha) * keyword_score) * match_boost * term_boost
            
            # Guardar scores
            result_data["combined_score"] = combined_score
            result_data["match_boost"] = match_boost
            result_data["term_boost"] = term_boost
            result_data["alpha_used"] = dynamic_alpha
        
        # Ordenar resultados por puntuación combinada
        sorted_results = sorted(
            combined_results.values(), 
            key=lambda x: x["combined_score"], 
            reverse=True
        )[:limit]
        
        # Convertir a objetos SearchResult
        results = []
        for result_data in sorted_results:
            result = SearchResult(
                id=result_data["id"],
                text=result_data["text"],
                score=float(result_data["combined_score"]),
                metadata={
                    **result_data["metadata"],
                    "semantic_score": result_data["semantic_score"],
                    "keyword_score": result_data["keyword_score"],
                    "match_boost": result_data["match_boost"],
                    "term_boost": result_data.get("term_boost", 1.0),
                    "alpha_used": result_data["alpha_used"],
                    "query": query
                }
            )
            results.append(result)
        
        logger.info(f"[🔍] Hybrid search with alpha={dynamic_alpha} found {len(results)} results with scores: {[round(r.score, 3) for r in results[:5]]}")
        
        return results
    
    async def get_dataset_embeddings(self, dataset_id: str) -> EmbeddingCollection:
        if dataset_id in self.embedding_cache:
            return self.embedding_cache[dataset_id]
        
        await self._load_dataset(dataset_id)
        
        if dataset_id not in self.embedding_cache:
            raise DatasetNotFoundException(dataset_id)
        
        return self.embedding_cache[dataset_id]
    
    async def save_search_results(self, results: SearchResults) -> None:        # En una implementación real, esto guardaría los resultados en una base de datos
        logger.info(f"Guardando resultados de búsqueda con ID {results.search_id}")
        
        pass
    
    async def get_search_results(self, search_id: str) -> Optional[SearchResults]:
        logger.info(f"Obteniendo resultados de búsqueda con ID {search_id}")
        
        return None
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas de rendimiento del sistema"""
        performance_metrics = self.performance_monitor.get_current_metrics()
        cache_stats = self.search_cache.get_cache_stats()
        quality_trends = self.quality_analyzer.get_quality_trends(days=7)
        
        return {
            "performance": {
                "avg_response_time_ms": performance_metrics.avg_response_time_ms,
                "p95_response_time_ms": performance_metrics.p95_response_time_ms,
                "p99_response_time_ms": performance_metrics.p99_response_time_ms,
                "queries_per_second": performance_metrics.queries_per_second,
                "error_rate": performance_metrics.error_rate,
                "total_queries": performance_metrics.total_queries
            },
            "cache": cache_stats,
            "quality": {
                "avg_quality_score": performance_metrics.avg_quality_score,
                "trends": quality_trends
            },
            "search_improvements": {
                "balanced_scoring": True,
                "result_diversification": True,
                "intelligent_caching": True,
                "quality_monitoring": True
            }
        }
    
    def clear_cache(self) -> Dict[str, Any]:
        """Limpia el caché de búsqueda"""
        cache_stats_before = self.search_cache.get_cache_stats()
        self.search_cache.clear_cache()
        
        return {
            "status": "success",
            "message": "Cache cleared successfully",
            "entries_cleared": cache_stats_before["total_entries"]
        }
    
    def invalidate_dataset_cache(self, dataset_id: str) -> Dict[str, Any]:
        """Invalida el caché para un dataset específico"""
        entries_invalidated = self.search_cache.invalidate_dataset(dataset_id)
        
        return {
            "status": "success",
            "message": f"Cache invalidated for dataset {dataset_id}",
            "entries_invalidated": entries_invalidated
        }
    
    def update_scoring_weights(self, new_weights: Dict[str, float]) -> Dict[str, Any]:
        """Actualiza los pesos de la estrategia de puntuación"""
        try:
            if hasattr(self.scoring_strategy, 'update_weights'):
                self.scoring_strategy.update_weights(new_weights)
                return {
                    "status": "success",
                    "message": "Scoring weights updated successfully",
                    "new_weights": new_weights
                }
            else:
                return {
                    "status": "error",
                    "message": "Current scoring strategy does not support weight updates"
                }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error updating weights: {str(e)}"
            }
    
    def configure_diversification(self, config_updates: Dict[str, Any]) -> Dict[str, Any]:
        """Actualiza la configuración de diversificación"""
        try:
            if "similarity_threshold" in config_updates:
                self.diversification_config.similarity_threshold = config_updates["similarity_threshold"]
            if "lambda_param" in config_updates:
                self.diversification_config.lambda_param = config_updates["lambda_param"]
            if "max_similar_results" in config_updates:
                self.diversification_config.max_similar_results = config_updates["max_similar_results"]
            if "enable_semantic_clustering" in config_updates:
                self.diversification_config.enable_semantic_clustering = config_updates["enable_semantic_clustering"]
            
            return {
                "status": "success",
                "message": "Diversification configuration updated successfully",
                "current_config": {
                    "similarity_threshold": self.diversification_config.similarity_threshold,
                    "lambda_param": self.diversification_config.lambda_param,
                    "max_similar_results": self.diversification_config.max_similar_results,
                    "enable_semantic_clustering": self.diversification_config.enable_semantic_clustering
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error updating diversification config: {str(e)}"
            }
    
    async def _load_dataset(self, dataset_id: str) -> None:
        try:            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.embedding_service_url}/datasets/{dataset_id}/embeddings?limit=5000",
                    timeout=30.0
                )
                
                if response.status_code == 404:
                    raise DatasetNotFoundException(dataset_id)
                
                if response.status_code != 200:
                    raise DataStorageConnectionException(
                        f"Error al obtener embeddings del dataset {dataset_id}: {response.text}"
                    )
                
                data = response.json()
                
                embeddings_data = data.get("embeddings", [])
                
                if not embeddings_data or len(embeddings_data) == 0:
                    raise ValueError(f"No se encontraron embeddings para el dataset {dataset_id}")
                
                embedding_collection = EmbeddingCollection(dataset_id=dataset_id)
                
                for i, embedding_vector in enumerate(embeddings_data):
                    embedding = EmbeddingVector(
                        vector=np.array(embedding_vector['vector'], dtype=np.float32),
                        text=embedding_vector['text'],           
                        metadata=embedding_vector['metadata'],
                        id=embedding_vector['row_id']
                    )
                    
                    embedding_collection.add_embedding(embedding)
                
                dimension = embedding_collection.dimension
                index = faiss.IndexFlatL2(dimension)
                
                vectors = embedding_collection.get_vectors()
                if len(vectors) > 0:
                    index.add(vectors)
                
                self.index_cache[dataset_id] = index
                self.embedding_cache[dataset_id] = embedding_collection

        except DatasetNotFoundException:
            raise
        except DataStorageConnectionException:
            raise
        except Exception as e:
            raise Exception(f"Error al cargar dataset {dataset_id}: {str(e)}")
