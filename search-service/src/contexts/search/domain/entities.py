from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
import numpy as np


@dataclass
class SearchResult:
    """Representa un resultado de búsqueda"""
    id: str
    text: str
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    data: Dict[str, Any] = field(default_factory=dict)
    row_id: str = ""


@dataclass
class SearchResults:
    """Representa una colección de resultados de búsqueda"""
    query: str
    results: List[SearchResult] = field(default_factory=list)
    total_results: int = 0
    execution_time_ms: float = 0.0
    dataset_id: Optional[str] = None
    search_id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=datetime.now)

    def add_result(self, result: SearchResult) -> None:
        """Añade un resultado a la colección"""
        self.results.append(result)
        self.total_results = len(self.results)


@dataclass
class EmbeddingVector:
    """Representa un vector de embedding"""
    vector: np.ndarray
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))

    def __post_init__(self):
        """Normaliza el vector después de la inicialización"""
        if not isinstance(self.vector, np.ndarray):
            self.vector = np.array(self.vector, dtype=np.float32)
        
        # Normalizar el vector
        norm = np.linalg.norm(self.vector)
        if norm > 0:
            self.vector = self.vector / norm


@dataclass
class EmbeddingCollection:
    """Representa una colección de vectores de embedding"""
    embeddings: List[EmbeddingVector] = field(default_factory=list)
    dataset_id: Optional[str] = None
    dimension: int = 0
    
    def add_embedding(self, embedding: EmbeddingVector) -> None:
        """Añade un embedding a la colección"""
        if self.dimension == 0 and embedding.vector is not None:
            self.dimension = embedding.vector.shape[0]
        
        self.embeddings.append(embedding)
    
    def get_vectors(self) -> np.ndarray:
        """Devuelve todos los vectores como una matriz numpy"""
        if not self.embeddings:
            return np.array([], dtype=np.float32)
        
        return np.vstack([e.vector for e in self.embeddings])
    
    def get_texts(self) -> List[str]:
        """Devuelve todos los textos"""
        return [e.text for e in self.embeddings]
    
    def get_metadata(self) -> List[Dict[str, Any]]:
        """Devuelve todos los metadatos"""
        return [e.metadata for e in self.embeddings]
    
    def get_ids(self) -> List[str]:
        """Devuelve todos los IDs"""
        return [e.id for e in self.embeddings] 