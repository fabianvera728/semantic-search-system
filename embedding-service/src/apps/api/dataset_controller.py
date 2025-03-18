from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request, Body, status
from pydantic import BaseModel

from ...contexts.embedding.application import (
    get_command_handlers,
    CreateDatasetRequestDTO,
    ProcessDatasetRowsRequestDTO
)

class DatasetController:
    def __init__(self):
        self.router = APIRouter(prefix="/datasets", tags=["datasets"])
        self._register_routes()
    
    def _register_routes(self):
        @self.router.post("", status_code=status.HTTP_201_CREATED)
        async def create_dataset(request: CreateDatasetRequestDTO):
            """Create a new dataset for storing embeddings."""
            handler = get_command_handlers()
            result = await handler.create_dataset_controller.execute(request.dict())
            
            if not result.success:
                raise HTTPException(status_code=result.status_code, detail=result.error)
                
            return result.data

        @self.router.post("/{dataset_id}/process", status_code=status.HTTP_200_OK)
        async def process_dataset_rows(
            dataset_id: str,
            request: ProcessDatasetRowsRequestDTO = None
        ):
            """Process rows from a dataset and generate embeddings."""
            handler = get_command_handlers()
            
            if request is None:
                request = ProcessDatasetRowsRequestDTO(dataset_id=dataset_id)
            elif request.dataset_id != dataset_id:
                request.dataset_id = dataset_id
            
            result = await handler.process_dataset_rows_controller.execute(request.dict())
            
            if not result.success:
                raise HTTPException(status_code=result.status_code, detail=result.error)
                
            return result.data

        @self.router.get("/{dataset_id}/embeddings")
        async def list_embeddings(
            dataset_id: str,
            limit: int = Query(100, ge=1, le=1000),
            offset: int = Query(0, ge=0),
            include_vectors: bool = Query(False)
        ):
            """List embeddings for a specific dataset."""
            from ...contexts.embedding.application import ListEmbeddingsRequestDTO
            
            handler = get_command_handlers()
            request = ListEmbeddingsRequestDTO(
                dataset_id=dataset_id,
                limit=limit,
                offset=offset,
                include_vectors=include_vectors
            )
            
            result = await handler.list_embeddings_controller.execute(request.dict())
            
            if not result.success:
                raise HTTPException(status_code=result.status_code, detail=result.error)
                
            return result.data

        @self.router.get("")
        async def list_datasets(
            limit: int = Query(100, ge=1, le=1000),
            offset: int = Query(0, ge=0)
        ):
            """List available datasets."""
            handler = get_command_handlers()
            result = await handler.handle_list_datasets(limit, offset)
            return result

        @self.router.get("/{dataset_id}")
        async def get_dataset(dataset_id: str):
            """Get information about a specific dataset."""
            handler = get_command_handlers()
            try:
                result = await handler.handle_get_dataset(dataset_id)
                return result
            except Exception as e:
                raise HTTPException(status_code=404, detail=str(e))

        @self.router.delete("/{dataset_id}")
        async def delete_dataset(dataset_id: str):
            """Delete a dataset and all its embeddings."""
            handler = get_command_handlers()
            try:
                result = await handler.handle_delete_dataset(dataset_id)
                return result
            except Exception as e:
                raise HTTPException(status_code=404, detail=str(e)) 