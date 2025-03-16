from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import uuid
import json
import httpx
from dotenv import load_dotenv

# Import embedding modules
from embedding.embedding_service import EmbeddingService
from utils.error_handler import ErrorHandler

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="NLP Service",
    description="Service for natural language processing and embeddings",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize embedding service
embedding_service = EmbeddingService()

# Models
class EmbeddingRequest(BaseModel):
    job_id: Optional[str] = None
    texts: List[str]
    config: Optional[Dict[str, Any]] = None

class SearchRequest(BaseModel):
    job_id: Optional[str] = None
    query: str
    dataset_id: str
    limit: Optional[int] = 10
    config: Optional[Dict[str, Any]] = None

class NLPResponse(BaseModel):
    job_id: str
    status: str
    message: str
    data: Optional[Dict[str, Any]] = None

# Routes
@app.get("/")
async def root():
    return {"message": "NLP Service is running"}

@app.post("/embed", response_model=NLPResponse)
async def generate_embeddings(request: EmbeddingRequest, background_tasks: BackgroundTasks):
    """Generate embeddings for a list of texts"""
    job_id = request.job_id or str(uuid.uuid4())
    
    # Start embedding in background
    background_tasks.add_task(
        process_embedding_job,
        job_id=job_id,
        texts=request.texts,
        config=request.config or {}
    )
    
    return {
        "job_id": job_id,
        "status": "started",
        "message": f"Embedding job started for {len(request.texts)} texts",
        "data": None
    }

@app.post("/search", response_model=NLPResponse)
async def search_similar(request: SearchRequest, background_tasks: BackgroundTasks):
    """Search for similar items based on a query"""
    job_id = request.job_id or str(uuid.uuid4())
    
    # Start search in background
    background_tasks.add_task(
        process_search_job,
        job_id=job_id,
        query=request.query,
        dataset_id=request.dataset_id,
        limit=request.limit,
        config=request.config or {}
    )
    
    return {
        "job_id": job_id,
        "status": "started",
        "message": f"Search job started for query: {request.query}",
        "data": None
    }

@app.get("/jobs/{job_id}", response_model=NLPResponse)
async def get_job_status(job_id: str):
    """Get the status of a job"""
    # In a real implementation, this would check a database or cache
    # For now, we'll just return a placeholder
    return {
        "job_id": job_id,
        "status": "unknown",
        "message": "Job status retrieval not implemented yet",
        "data": None
    }

@app.get("/models")
async def get_available_models():
    """Get all available NLP models"""
    return {
        "models": [
            {
                "id": "sentence-transformers/all-MiniLM-L6-v2",
                "name": "all-MiniLM-L6-v2",
                "description": "Sentence transformer model for generating embeddings",
                "dimensions": 384
            },
            {
                "id": "sentence-transformers/all-mpnet-base-v2",
                "name": "all-mpnet-base-v2",
                "description": "Sentence transformer model for generating embeddings",
                "dimensions": 768
            },
            {
                "id": "spacy/en_core_web_md",
                "name": "en_core_web_md",
                "description": "spaCy model for NLP tasks",
                "dimensions": 300
            }
        ]
    }

# Background task for processing embedding jobs
async def process_embedding_job(job_id: str, texts: List[str], config: Dict[str, Any]):
    """Process an embedding job in the background"""
    result = None
    status = "processing"
    error = None
    
    try:
        # Generate embeddings
        embeddings = embedding_service.generate_embeddings(texts)
        
        # Set result
        result = {
            "embeddings": embeddings.tolist(),
            "texts_processed": len(texts),
            "embedding_dimensions": embeddings.shape[1]
        }
        
        status = "completed"
    except Exception as e:
        status = "failed"
        error = str(e)
        print(f"Error processing embedding job {job_id}: {error}")
    
    # Notify orchestrator about job completion
    try:
        orchestrator_url = os.getenv("ORCHESTRATOR_URL", "http://localhost:8000")
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{orchestrator_url}/jobs/update",
                json={
                    "job_id": job_id,
                    "service": "nlp-service",
                    "status": status,
                    "result": result,
                    "error": error
                }
            )
    except Exception as e:
        print(f"Error notifying orchestrator: {str(e)}")

# Background task for processing search jobs
async def process_search_job(job_id: str, query: str, dataset_id: str, limit: int, config: Dict[str, Any]):
    """Process a search job in the background"""
    result = None
    status = "processing"
    error = None
    
    try:
        # Search for similar items
        similar_items = embedding_service.search(query, dataset_id, limit)
        
        # Set result
        result = {
            "query": query,
            "dataset_id": dataset_id,
            "similar_items": similar_items,
            "total_results": len(similar_items)
        }
        
        status = "completed"
    except Exception as e:
        status = "failed"
        error = str(e)
        print(f"Error processing search job {job_id}: {error}")
    
    # Notify orchestrator about job completion
    try:
        orchestrator_url = os.getenv("ORCHESTRATOR_URL", "http://localhost:8000")
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{orchestrator_url}/jobs/update",
                json={
                    "job_id": job_id,
                    "service": "nlp-service",
                    "status": status,
                    "result": result,
                    "error": error
                }
            )
    except Exception as e:
        print(f"Error notifying orchestrator: {str(e)}")

# Error handlers
app.add_exception_handler(ValueError, ErrorHandler.value_error_handler)
app.add_exception_handler(Exception, ErrorHandler.general_exception_handler)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 