from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
import numpy as np


@dataclass
class Embedding:
    vector: np.ndarray
    text: str
    dataset_id: str
    row_id: str
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not isinstance(self.vector, np.ndarray):
            self.vector = np.array(self.vector, dtype=np.float32)
        
        # Normalize vector for cosine similarity
        norm = np.linalg.norm(self.vector)
        if norm > 0:
            self.vector = self.vector / norm


@dataclass
class EmbeddingBatch:
    embeddings: List[Embedding] = field(default_factory=list)
    dataset_id: str = ""
    batch_id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_embedding(self, embedding: Embedding) -> None:
        self.embeddings.append(embedding)
    
    def get_vectors(self) -> np.ndarray:
        if not self.embeddings:
            return np.array([], dtype=np.float32)
        
        return np.vstack([e.vector for e in self.embeddings])
    
    def get_texts(self) -> List[str]:
        return [e.text for e in self.embeddings]
    
    def get_row_ids(self) -> List[str]:
        return [e.row_id for e in self.embeddings]
    
    def get_metadata(self) -> List[Dict[str, Any]]:
        return [e.metadata for e in self.embeddings]


@dataclass
class Dataset:
    id: str
    name: str
    created_at: datetime
    updated_at: datetime
    embedding_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def collection_name(self) -> str:
        return f"dataset_{self.id}"


@dataclass
class EmbeddingModel:
    name: str
    dimension: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_sentence_transformer(self) -> bool:
        return self.name.startswith("sentence-transformers/") or "sentence-transformers" in self.metadata.get("type", "") 