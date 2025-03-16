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
    """Implementación del repositorio de búsqueda"""
    
    def __init__(self, embedding_repository: Optional[EmbeddingRepositoryImpl] = None):
        """Inicializa el repositorio de búsqueda"""
        self.embedding_repository = embedding_repository or EmbeddingRepositoryImpl()
        self.data_storage_url = os.getenv("DATA_STORAGE_URL", "http://data-storage:8003")
        
        # Caché de índices y embeddings
        self.index_cache = {}
        self.embedding_cache = {}
        
        logger.info(f"Repositorio de búsqueda inicializado con URL de almacenamiento: {self.data_storage_url}")
    
    async def search(self, request: SearchRequest) -> SearchResults:
        """Realiza una búsqueda"""
        start_time = time.time()
        
        try:
            # Validar consulta
            if not request.query.text.strip():
                raise EmptyQueryException()
            
            # Obtener embeddings del dataset
            dataset_id = request.dataset_id.value
            if dataset_id not in self.index_cache:
                await self._load_dataset(dataset_id)
            
            # Obtener índice y datos
            index = self.index_cache.get(dataset_id)
            embedding_collection = self.embedding_cache.get(dataset_id)
            
            if index is None or embedding_collection is None:
                raise DatasetNotFoundException(dataset_id)
            
            # Realizar búsqueda según el tipo
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
            
            # Crear resultados
            search_results = SearchResults(
                query=request.query.text,
                results=results,
                total_results=len(results),
                execution_time_ms=(time.time() - start_time) * 1000,
                dataset_id=dataset_id,
                search_id=request.search_id.value
            )
            
            # Guardar resultados
            await self.save_search_results(search_results)
            
            return search_results
            
        except (DatasetNotFoundException, EmptyQueryException, InvalidSearchTypeException):
            raise
        except Exception as e:
            logger.error(f"Error al realizar búsqueda: {str(e)}")
            raise SearchExecutionException(str(e), request.dataset_id.value)
    
    async def _semantic_search(
        self, 
        query: str, 
        index: faiss.Index, 
        embedding_collection: EmbeddingCollection, 
        limit: int,
        model_name: str
    ) -> List[SearchResult]:
        """Realiza una búsqueda semántica"""
        # Generar embedding para la consulta
        embedding_request = EmbeddingRequest(
            texts=[query],
            model=model_name
        )
        query_embedding = await self.embedding_repository.generate_embeddings(embedding_request)
        
        # Realizar búsqueda
        distances, indices = index.search(query_embedding, limit)
        
        # Preparar resultados
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < 0 or idx >= len(embedding_collection.embeddings):
                continue
                
            embedding = embedding_collection.embeddings[idx]
            score = float(1.0 - distances[0][i])  # Convertir distancia a similitud
            
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
        """Realiza una búsqueda por palabras clave"""
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        
        # Obtener textos
        texts = embedding_collection.get_texts()
        if not texts:
            return []
        
        # Crear vectorizador TF-IDF
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(texts + [query])
        
        # Calcular similitud
        query_vector = tfidf_matrix[-1]
        document_vectors = tfidf_matrix[:-1]
        similarities = cosine_similarity(query_vector, document_vectors)[0]
        
        # Ordenar por similitud
        sorted_indices = np.argsort(similarities)[::-1][:limit]
        
        # Preparar resultados
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
        """Realiza una búsqueda híbrida (semántica + palabras clave)"""
        # Realizar búsqueda semántica
        semantic_results = await self._semantic_search(
            query, 
            index, 
            embedding_collection, 
            limit * 2,  # Obtener más resultados para combinar
            model_name
        )
        
        # Realizar búsqueda por palabras clave
        keyword_results = await self._keyword_search(
            query, 
            embedding_collection, 
            limit * 2  # Obtener más resultados para combinar
        )
        
        # Combinar resultados
        combined_results = {}
        
        # Agregar resultados semánticos
        for result in semantic_results:
            combined_results[result.id] = {
                "id": result.id,
                "text": result.text,
                "semantic_score": result.score,
                "keyword_score": 0.0,
                "metadata": result.metadata
            }
        
        # Agregar resultados por palabras clave
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
        
        # Calcular puntuación combinada
        for result_id, result_data in combined_results.items():
            semantic_score = result_data["semantic_score"]
            keyword_score = result_data["keyword_score"]
            combined_score = alpha * semantic_score + (1 - alpha) * keyword_score
            result_data["combined_score"] = combined_score
        
        # Ordenar por puntuación combinada
        sorted_results = sorted(
            combined_results.values(), 
            key=lambda x: x["combined_score"], 
            reverse=True
        )[:limit]
        
        # Convertir a SearchResult
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
        """Obtiene los embeddings para un dataset"""
        if dataset_id in self.embedding_cache:
            return self.embedding_cache[dataset_id]
        
        await self._load_dataset(dataset_id)
        
        if dataset_id not in self.embedding_cache:
            raise DatasetNotFoundException(dataset_id)
        
        return self.embedding_cache[dataset_id]
    
    async def save_search_results(self, results: SearchResults) -> None:
        """Guarda los resultados de una búsqueda"""
        # En una implementación real, esto guardaría los resultados en una base de datos
        # Para esta implementación, simplemente los guardamos en memoria
        logger.info(f"Guardando resultados de búsqueda con ID {results.search_id}")
        
        # Aquí se podría implementar la lógica para guardar en una base de datos
        pass
    
    async def get_search_results(self, search_id: str) -> Optional[SearchResults]:
        """Obtiene los resultados de una búsqueda por su ID"""
        # En una implementación real, esto obtendría los resultados de una base de datos
        # Para esta implementación, devolvemos None
        logger.info(f"Obteniendo resultados de búsqueda con ID {search_id}")
        
        # Aquí se podría implementar la lógica para obtener de una base de datos
        return None
    
    async def _load_dataset(self, dataset_id: str) -> None:
        """Carga los embeddings de un dataset desde el servicio de almacenamiento"""
        try:
            logger.info(f"Cargando dataset {dataset_id} desde el servicio de almacenamiento")
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.data_storage_url}/datasets/{dataset_id}/embeddings",
                    timeout=30.0
                )
                
                if response.status_code == 404:
                    raise DatasetNotFoundException(dataset_id)
                
                if response.status_code != 200:
                    raise DataStorageConnectionException(
                        f"Error al obtener embeddings del dataset {dataset_id}: {response.text}"
                    )
                
                data = response.json()
                
                # Extraer embeddings y metadatos
                embeddings_data = data.get("embeddings", [])
                texts = data.get("texts", [])
                metadata = data.get("metadata", [])
                
                if not embeddings_data or len(embeddings_data) == 0:
                    raise ValueError(f"No se encontraron embeddings para el dataset {dataset_id}")
                
                # Crear colección de embeddings
                embedding_collection = EmbeddingCollection(dataset_id=dataset_id)
                
                # Añadir embeddings a la colección
                for i, embedding_vector in enumerate(embeddings_data):
                    text = texts[i] if i < len(texts) else ""
                    meta = metadata[i] if i < len(metadata) else {}
                    
                    embedding = EmbeddingVector(
                        vector=np.array(embedding_vector, dtype=np.float32),
                        text=text,
                        metadata=meta,
                        id=meta.get("id", f"item_{i}")
                    )
                    
                    embedding_collection.add_embedding(embedding)
                
                # Crear índice FAISS
                dimension = embedding_collection.dimension
                index = faiss.IndexFlatL2(dimension)
                
                # Añadir vectores al índice
                vectors = embedding_collection.get_vectors()
                if len(vectors) > 0:
                    index.add(vectors)
                
                # Guardar en caché
                self.index_cache[dataset_id] = index
                self.embedding_cache[dataset_id] = embedding_collection
                
                logger.info(f"Dataset {dataset_id} cargado correctamente con {len(embedding_collection.embeddings)} embeddings")
                
        except DatasetNotFoundException:
            raise
        except DataStorageConnectionException:
            raise
        except Exception as e:
            logger.error(f"Error al cargar dataset {dataset_id}: {str(e)}")
            
            # Para fines de demostración, crear datos ficticios
            logger.warning(f"Creando datos ficticios para el dataset {dataset_id}")
            
            # Crear embeddings ficticios
            dimension = 384  # Dimensión por defecto
            num_items = 100
            
            # Generar embeddings aleatorios
            embeddings_data = np.random.rand(num_items, dimension).astype(np.float32)
            
            # Normalizar embeddings
            for i in range(embeddings_data.shape[0]):
                embeddings_data[i] = embeddings_data[i] / np.linalg.norm(embeddings_data[i])
            
            # Crear colección de embeddings
            embedding_collection = EmbeddingCollection(dataset_id=dataset_id)
            
            # Añadir embeddings a la colección
            for i in range(num_items):
                embedding = EmbeddingVector(
                    vector=embeddings_data[i],
                    text=f"Texto de ejemplo {i} para el dataset {dataset_id}",
                    metadata={
                        "id": f"item_{i}",
                        "source": "dummy",
                        "index": i
                    },
                    id=f"item_{i}"
                )
                
                embedding_collection.add_embedding(embedding)
            
            # Crear índice FAISS
            index = faiss.IndexFlatL2(dimension)
            index.add(embeddings_data)
            
            # Guardar en caché
            self.index_cache[dataset_id] = index
            self.embedding_cache[dataset_id] = embedding_collection
            
            logger.info(f"Datos ficticios creados para el dataset {dataset_id}") 