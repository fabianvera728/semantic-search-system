from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request, Body, status
from pydantic import UUID4

from ...contexts.embedding.application import (
    get_command_handlers,
    GenerateEmbeddingRequestDTO,
    BatchEmbeddingRequestDTO,
    DeleteEmbeddingRequestDTO,
    GetEmbeddingRequestDTO,
    ListEmbeddingsRequestDTO
)

class EmbeddingController:
    def __init__(self):
        self.router = APIRouter(prefix="/embeddings", tags=["embeddings"])
        self._register_routes()
    
    def _register_routes(self):
        @self.router.post("", status_code=status.HTTP_201_CREATED)
        async def generate_embedding(request: GenerateEmbeddingRequestDTO):
            """Generate a single embedding for a text."""
            handler = get_command_handlers()
            result = await handler.generate_embedding_controller.execute(request.dict())
            
            if not result.success:
                raise HTTPException(status_code=result.status_code, detail=result.error)
                
            return result.data

        @self.router.post("/batch", status_code=status.HTTP_201_CREATED)
        async def generate_batch_embeddings(request: BatchEmbeddingRequestDTO):
            """Generate embeddings for multiple texts."""
            handler = get_command_handlers()
            result = await handler.generate_batch_embeddings_controller.execute(request.dict())
            
            if not result.success:
                raise HTTPException(status_code=result.status_code, detail=result.error)
                
            return result.data

        @self.router.get("/{embedding_id}")
        async def get_embedding(
            embedding_id: UUID4,
            dataset_id: Optional[str] = Query(None),
            include_vector: bool = Query(False)
        ):
            """Get a specific embedding by ID."""
            handler = get_command_handlers()
            request = GetEmbeddingRequestDTO(
                embedding_id=embedding_id,
                dataset_id=dataset_id,
                include_vector=include_vector
            )
            
            result = await handler.get_embedding_controller.execute(request.dict())
            
            if not result.success:
                raise HTTPException(status_code=result.status_code, detail=result.error)
                
            return result.data

        @self.router.delete("/{embedding_id}")
        async def delete_embedding(
            embedding_id: UUID4,
            dataset_id: Optional[str] = Query(None)
        ):
            """Delete a specific embedding by ID."""
            handler = get_command_handlers()
            request = DeleteEmbeddingRequestDTO(
                embedding_id=embedding_id,
                dataset_id=dataset_id
            )
            
            result = await handler.delete_embedding_controller.execute(request.dict())
            
            if not result.success:
                raise HTTPException(status_code=result.status_code, detail=result.error)
                
            return result.data

        @self.router.get("/models")
        async def get_embedding_models():
            """List available embedding models."""
            handler = get_command_handlers()
            result = await handler.handle_get_embedding_models()
            return result 