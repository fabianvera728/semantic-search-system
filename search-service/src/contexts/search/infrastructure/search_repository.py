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
        embedding_request = EmbeddingRequest(
            texts=[query],
            model=model_name
        )
        query_embedding = await self.embedding_repository.generate_embeddings(embedding_request)
        
        distances, indices = index.search(query_embedding, limit)

        logger.info(f"[📏] Metric type: {index.metric_type}")
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < 0 or idx >= len(embedding_collection.embeddings):
                continue
                
            embedding = embedding_collection.embeddings[idx]
            logger.info(f"[🔍] Distances: {distances}")
            logger.info(f"[🔍] Indices: {indices}")
            score = float(1.0 - distances[0][i])
            
            result = SearchResult(
                id=embedding.id,
                text=embedding.text,
                score=score,
                metadata=embedding.metadata
            )
            results.append(result)
        
        return results
    
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
        semantic_results = await self._semantic_search(
            query, 
            index, 
            embedding_collection, 
            limit * 2,
            model_name
        )
        
        keyword_results = await self._keyword_search(
            query, 
            embedding_collection, 
            limit * 2
        )
        
        combined_results = {}
        
        for result in semantic_results:
            combined_results[result.id] = {
                "id": result.id,
                "text": result.text,
                "semantic_score": result.score,
                "keyword_score": 0.0,
                "metadata": result.metadata
            }
        
        for result in keyword_results:
            if result.id in combined_results:
                combined_results[result.id]["keyword_score"] = result.score
            else:
                combined_results[result.id] = {
                    "id": result.id,
                    "text": result.text,
                    "semantic_score": 0.0,
                    "keyword_score": result.score,
                    "metadata": result.metadata
                }
        
        for result_id, result_data in combined_results.items():
            semantic_score = result_data["semantic_score"]
            keyword_score = result_data["keyword_score"]
            combined_score = alpha * semantic_score + (1 - alpha) * keyword_score
            result_data["combined_score"] = combined_score
        
        sorted_results = sorted(
            combined_results.values(), 
            key=lambda x: x["combined_score"], 
            reverse=True
        )[:limit]
        
        results = []
        for result_data in sorted_results:
            result = SearchResult(
                id=result_data["id"],
                text=result_data["text"],
                score=float(result_data["combined_score"]),
                metadata={
                    **result_data["metadata"],
                    "semantic_score": result_data["semantic_score"],
                    "keyword_score": result_data["keyword_score"]
                }
            )
            results.append(result)
        
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
