import os
import numpy as np
import torch
from typing import List, Dict, Any, Optional, Union
from sentence_transformers import SentenceTransformer
import faiss
import httpx
import json

class EmbeddingService:
    """Service for generating embeddings and searching."""
    
    def __init__(self):
        # Load model
        model_name = os.getenv("NLP_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        self.model = SentenceTransformer(model_name)
        
        # Initialize index cache
        self.index_cache = {}
        self.embedding_cache = {}
    
    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for a list of texts."""
        # Check if texts is empty
        if not texts:
            return np.array([])
        
        # Generate embeddings
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        
        return embeddings
    
    async def search(self, query: str, dataset_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for similar items based on a query."""
        # Generate query embedding
        query_embedding = self.model.encode(query, convert_to_numpy=True)
        
        # Get or create index for dataset
        if dataset_id not in self.index_cache:
            await self._load_dataset(dataset_id)
        
        # Get index and data
        index = self.index_cache.get(dataset_id)
        data = self.embedding_cache.get(dataset_id, {}).get("data", [])
        
        if index is None or not data:
            raise ValueError(f"Dataset {dataset_id} not found or has no embeddings")
        
        # Search for similar items
        distances, indices = index.search(np.array([query_embedding]), limit)
        
        # Prepare results
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < 0 or idx >= len(data):
                continue
                
            item = data[idx].copy()
            item["score"] = float(1.0 - distances[0][i])  # Convert distance to similarity score
            results.append(item)
        
        return results
    
    async def _load_dataset(self, dataset_id: str):
        """Load dataset embeddings and create index."""
        # In a real implementation, this would load from a database or storage service
        # For now, we'll just make a request to the data-storage service
        try:
            storage_url = os.getenv("DATA_STORAGE_URL", "http://data-storage:8000")
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{storage_url}/datasets/{dataset_id}/embeddings")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Extract embeddings and items
                    embeddings = np.array(data.get("embeddings", []), dtype=np.float32)
                    items = data.get("items", [])
                    
                    if len(embeddings) == 0:
                        raise ValueError(f"No embeddings found for dataset {dataset_id}")
                    
                    # Create index
                    dimension = embeddings.shape[1]
                    index = faiss.IndexFlatL2(dimension)
                    index.add(embeddings)
                    
                    # Cache index and data
                    self.index_cache[dataset_id] = index
                    self.embedding_cache[dataset_id] = {
                        "embeddings": embeddings,
                        "data": items
                    }
                else:
                    raise ValueError(f"Failed to load dataset {dataset_id}: {response.text}")
        except Exception as e:
            # For demo purposes, create a dummy index
            print(f"Error loading dataset {dataset_id}: {str(e)}")
            print("Creating dummy index for demonstration")
            
            # Create dummy embeddings and data
            dimension = 384  # Default dimension for all-MiniLM-L6-v2
            num_items = 100
            
            # Generate random embeddings
            embeddings = np.random.rand(num_items, dimension).astype(np.float32)
            
            # Normalize embeddings
            for i in range(embeddings.shape[0]):
                embeddings[i] = embeddings[i] / np.linalg.norm(embeddings[i])
            
            # Create dummy data
            items = []
            for i in range(num_items):
                items.append({
                    "id": f"item_{i}",
                    "text": f"This is a dummy item {i} for dataset {dataset_id}",
                    "metadata": {
                        "source": "dummy",
                        "index": i
                    }
                })
            
            # Create index
            index = faiss.IndexFlatL2(dimension)
            index.add(embeddings)
            
            # Cache index and data
            self.index_cache[dataset_id] = index
            self.embedding_cache[dataset_id] = {
                "embeddings": embeddings,
                "data": items
            }