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

from .embedding_repository import EmbeddingRepositoryImpl
from ..domain.value_objects import EmbeddingRequest

logger = logging.getLogger(__name__)


class SearchRepositoryImpl(SearchRepository):
    
    def __init__(self, embedding_repository: Optional[EmbeddingRepositoryImpl] = None):
        self.embedding_repository = embedding_repository or EmbeddingRepositoryImpl()
        self.data_storage_url = os.getenv("DATA_STORAGE_URL", "http://data-storage:8003")
        self.embedding_service_url = os.getenv("EMBEDDING_SERVICE_URL", "http://embedding-service:8005")
        
        self.index_cache = {}
        self.embedding_cache = {}
        
        logger.info(f"Repositorio de búsqueda inicializado con URL de almacenamiento: {self.data_storage_url}")
    
    async def search(self, request: SearchRequest) -> SearchResults:
        start_time = time.time()
        
        try:
            if not request.query.text.strip():
                raise EmptyQueryException()
            
            dataset_id = request.dataset_id.value
            if dataset_id not in self.index_cache:
                await self._load_dataset(dataset_id)
            
            index = self.index_cache.get(dataset_id)
            embedding_collection = self.embedding_cache.get(dataset_id)
            
            if index is None or embedding_collection is None:
                raise DatasetNotFoundException(dataset_id)
            
            search_type = request.config.search_type
            limit = request.config.limit
            
            if search_type == "semantic":
                results = await self._semantic_search(
                    request.query.text, 
                    index, 
                    embedding_collection, 
                    limit,
                    request.config.embedding_model
                )
            elif search_type == "keyword":
                results = await self._keyword_search(
                    request.query.text, 
                    embedding_collection, 
                    limit
                )
            elif search_type == "hybrid":
                results = await self._hybrid_search(
                    request.query.text, 
                    index, 
                    embedding_collection, 
                    limit,
                    request.config.embedding_model,
                    request.config.hybrid_alpha
                )
            else:
                raise InvalidSearchTypeException(search_type)
            
            new_results = []
            for result in results:
                row_data = await self._get_row_data(dataset_id, result.id)
                result.data = row_data.get("data", {})
                new_results.append(result)

            search_results = SearchResults(
                query=request.query.text,
                results=results,
                total_results=len(results),
                execution_time_ms=(time.time() - start_time) * 1000,
                dataset_id=dataset_id,
                search_id=request.search_id.value
            )
            
            await self.save_search_results(search_results)
            
            return search_results
            
        except (DatasetNotFoundException, EmptyQueryException, InvalidSearchTypeException):
            raise
        except Exception as e:
            logger.error(f"Error al realizar búsqueda: {str(e)}")
            raise SearchExecutionException(str(e), request.dataset_id.value)
    
    async def _get_row_data(self, dataset_id: str, row_id: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.data_storage_url}/datasets/{dataset_id}/rows/{row_id}",
                timeout=30.0
            )
            return response.json()

    async def _semantic_search(
        self, 
        query: str, 
        index: faiss.Index, 
        embedding_collection: EmbeddingCollection, 
        limit: int,
        model_name: str
    ) -> List[SearchResult]:
        # Preprocesamiento de la consulta
        clean_query = query.strip()
        
        # Generar embedding para la consulta
        embedding_request = EmbeddingRequest(
            texts=[clean_query],
            model=model_name
        )
        query_embedding = await self.embedding_repository.generate_embeddings(embedding_request)
        
        # Búsqueda en el índice FAISS - aumentar el número de resultados iniciales para filtrar después
        search_limit = min(limit * 3, len(embedding_collection.embeddings))
        distances, indices = index.search(query_embedding, search_limit)

        logger.info(f"[📏] Metric type: {index.metric_type}")
        logger.info(f"[🔍] Query: {clean_query}")
        logger.info(f"[🔍] Found {len(indices[0])} initial matches")
        
        # Normalizar las distancias para obtener mejores puntuaciones de relevancia
        max_distance = np.max(distances[0]) if len(distances[0]) > 0 else 1.0
        min_distance = np.min(distances[0]) if len(distances[0]) > 0 else 0.0
        distance_range = max(max_distance - min_distance, 1e-5)  # Evitar división por cero
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < 0 or idx >= len(embedding_collection.embeddings):
                continue
                
            embedding = embedding_collection.embeddings[idx]
            
            # Cálculo mejorado de la puntuación de relevancia
            normalized_distance = (distances[0][i] - min_distance) / distance_range
            base_score = 1.0 - normalized_distance
            
            # Amplificar las puntuaciones usando una función sigmoide
            amplified_score = 1.0 / (1.0 + np.exp(-10 * (base_score - 0.5)))
            
            # Calcular score alternativo con transformación exponencial
            # Este enfoque da mayor contraste entre resultados buenos y mediocres
            alt_score = float(np.exp(-distances[0][i]))
            
            # Otro score alternativo basado en la distancia original
            alt_score2 = float(1 / (1 + np.sqrt(distances[0][i])))
            
            # Seleccionar el mejor score entre los diferentes métodos
            final_score = max(amplified_score, alt_score, alt_score2)
            
            # Ajustar el score con un boost de términos exactos si hay coincidencias directas
            query_terms = set(clean_query.lower().split())
            text_terms = set(embedding.text.lower().split())
            exact_match_ratio = len(query_terms.intersection(text_terms)) / len(query_terms) if query_terms else 0
            
            # Aplicar boost por coincidencias exactas
            term_boost = 1.0 + (exact_match_ratio * 0.3)  # Hasta 30% de boost por coincidencias exactas
            final_score = final_score * term_boost
            
            # Capear el score a 1.0 máximo
            final_score = min(final_score, 1.0)
            
            # Añadir información de depuración/explicación a los metadatos
            metadata = {
                **embedding.metadata,
                "raw_distance": float(distances[0][i]),
                "normalized_distance": float(normalized_distance),
                "base_score": float(base_score),
                "amplified_score": float(amplified_score),
                "alt_score": float(alt_score),
                "alt_score2": float(alt_score2),
                "term_boost": float(term_boost),
                "exact_match_ratio": float(exact_match_ratio),
                "final_score": float(final_score),
                "query": clean_query
            }
            
            result = SearchResult(
                id=embedding.id,
                text=embedding.text,
                score=final_score,
                metadata=metadata
            )
            results.append(result)
        
        # Ordenar por score y limitar a los mejores resultados
        results.sort(key=lambda x: x.score, reverse=True)
        top_results = results[:limit]
        
        logger.info(f"[🔍] Returning {len(top_results)} filtered matches with scores: {[round(r.score, 3) for r in top_results[:5]]}")
        
        return top_results
    
    async def _keyword_search(
        self, 
        query: str, 
        embedding_collection: EmbeddingCollection, 
        limit: int
    ) -> List[SearchResult]:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        
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
