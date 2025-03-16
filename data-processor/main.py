from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import uuid
import json
import httpx
from dotenv import load_dotenv

# Import preprocessing modules
from preprocessing.preprocessor import Preprocessor
from preprocessing.preprocessing_factory import PreprocessingFactory
from utils.error_handler import ErrorHandler

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Data Processor Service",
    description="Service for preprocessing and transforming data",
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

# Initialize preprocessing factory
preprocessing_factory = PreprocessingFactory()

# Models
class ProcessRequest(BaseModel):
    job_id: Optional[str] = None
    dataset: List[Dict[str, Any]]
    operations: List[Dict[str, Any]]
    config: Optional[Dict[str, Any]] = None

class ProcessResponse(BaseModel):
    job_id: str
    status: str
    message: str
    data: Optional[Dict[str, Any]] = None

# Routes
@app.get("/")
async def root():
    return {"message": "Data Processor Service is running"}

@app.post("/process", response_model=ProcessResponse)
async def process_data(request: ProcessRequest, background_tasks: BackgroundTasks):
    """Start a data processing job"""
    job_id = request.job_id or str(uuid.uuid4())
    
    # Start processing in background
    background_tasks.add_task(
        process_data_job,
        job_id=job_id,
        dataset=request.dataset,
        operations=request.operations,
        config=request.config or {}
    )
    
    return {
        "job_id": job_id,
        "status": "started",
        "message": f"Processing job started with {len(request.operations)} operations",
        "data": None
    }

@app.get("/jobs/{job_id}", response_model=ProcessResponse)
async def get_job_status(job_id: str):
    """Get the status of a processing job"""
    # In a real implementation, this would check a database or cache
    # For now, we'll just return a placeholder
    return {
        "job_id": job_id,
        "status": "unknown",
        "message": "Job status retrieval not implemented yet",
        "data": None
    }

@app.get("/operations")
async def get_available_operations():
    """Get all available preprocessing operations"""
    return {
        "operations": [
            {
                "id": "text-cleaning",
                "name": "Text Cleaning",
                "description": "Clean text data by removing special characters, HTML tags, etc.",
                "parameters": {
                    "remove_html": "boolean",
                    "remove_urls": "boolean",
                    "remove_special_chars": "boolean"
                }
            },
            {
                "id": "text-normalization",
                "name": "Text Normalization",
                "description": "Normalize text by converting to lowercase, removing accents, etc.",
                "parameters": {
                    "lowercase": "boolean",
                    "remove_accents": "boolean",
                    "remove_stopwords": "boolean"
                }
            },
            {
                "id": "text-tokenization",
                "name": "Text Tokenization",
                "description": "Tokenize text into words or sentences",
                "parameters": {
                    "tokenize_type": "string",
                    "min_token_length": "number"
                }
            },
            {
                "id": "missing-data",
                "name": "Missing Data Handling",
                "description": "Handle missing data in the dataset",
                "parameters": {
                    "strategy": "string",
                    "fill_value": "string"
                }
            },
            {
                "id": "data-transformation",
                "name": "Data Transformation",
                "description": "Transform data using various methods",
                "parameters": {
                    "method": "string",
                    "columns": "array"
                }
            }
        ]
    }

# Background task for processing data
async def process_data_job(job_id: str, dataset: List[Dict[str, Any]], operations: List[Dict[str, Any]], config: Dict[str, Any]):
    """Process a data job in the background"""
    result = None
    status = "processing"
    error = None
    
    try:
        # Create preprocessor
        preprocessor = Preprocessor()
        
        # Apply operations
        processed_data = dataset
        for operation in operations:
            operation_id = operation.get("id")
            parameters = operation.get("parameters", {})
            
            # Get operation handler
            operation_handler = preprocessing_factory.get_operation(operation_id)
            
            # Apply operation
            processed_data = operation_handler.process(processed_data, parameters)
        
        # Set result
        result = {
            "processed_items": len(processed_data),
            "operations_applied": len(operations),
            "data": processed_data
        }
        
        status = "completed"
    except Exception as e:
        status = "failed"
        error = str(e)
        print(f"Error processing job {job_id}: {error}")
    
    # Notify orchestrator about job completion
    try:
        orchestrator_url = os.getenv("ORCHESTRATOR_URL", "http://localhost:8000")
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{orchestrator_url}/jobs/update",
                json={
                    "job_id": job_id,
                    "service": "data-processor",
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