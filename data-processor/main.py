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

# Job storage in memory (in production this would be a database)
jobs_store: Dict[str, Dict[str, Any]] = {}

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

@app.get("/operations")
async def get_available_operations():
    """Get available preprocessing operations"""
    try:
        operations = preprocessing_factory.get_available_operations()
        return {"operations": operations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting operations: {str(e)}")

@app.post("/test")
async def test_processing_config(request: ProcessRequest):
    """Test a processing configuration with sample data"""
    try:
        # Create preprocessor
        preprocessor = Preprocessor()
        
        # Apply operations to sample data
        processed_data = request.dataset
        for operation in request.operations:
            operation_id = operation.get("id")
            parameters = operation.get("parameters", {})
            
            # Get operation handler
            operation_handler = preprocessing_factory.get_operation(operation_id)
            
            # Apply operation
            processed_data = operation_handler.process(processed_data, parameters)
        
        return {
            "success": True,
            "message": f"Successfully processed {len(processed_data)} items with {len(request.operations)} operations",
            "result": processed_data[:5] if len(processed_data) > 5 else processed_data  # Return first 5 items as preview
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error testing processing config: {str(e)}"
        }

@app.post("/process", response_model=ProcessResponse)
async def process_data(request: ProcessRequest, background_tasks: BackgroundTasks):
    """Start a data processing job"""
    job_id = request.job_id or str(uuid.uuid4())
    
    # Initialize job in store
    jobs_store[job_id] = {
        "job_id": job_id,
        "status": "started",
        "message": f"Processing job started with {len(request.operations)} operations",
        "data": None,
        "error": None
    }
    
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
    if job_id not in jobs_store:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job_data = jobs_store[job_id]
    return {
        "job_id": job_data["job_id"],
        "status": job_data["status"],
        "message": job_data["message"],
        "data": job_data["data"]
    }

# Background task for processing data
async def process_data_job(job_id: str, dataset: List[Dict[str, Any]], operations: List[Dict[str, Any]], config: Dict[str, Any]):
    """Process a data job in the background"""
    result = None
    status = "processing"
    error = None
    
    try:
        # Update job status to processing
        if job_id in jobs_store:
            jobs_store[job_id]["status"] = "processing"
            jobs_store[job_id]["message"] = "Processing data..."
        
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
        message = f"Successfully processed {len(processed_data)} items with {len(operations)} operations"
        
    except Exception as e:
        status = "failed"
        error = str(e)
        message = f"Error processing job: {error}"
        print(f"Error processing job {job_id}: {error}")
    
    # Update job status in store
    if job_id in jobs_store:
        jobs_store[job_id].update({
                    "status": status,
            "message": message,
            "data": result,
                    "error": error
        })
    
    print(f"Job {job_id} completed with status: {status}")

# Error handlers
app.add_exception_handler(ValueError, ErrorHandler.value_error_handler)
app.add_exception_handler(Exception, ErrorHandler.general_exception_handler)

if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment variable
    port = int(os.getenv("DATA_PROCESSOR_PORT", "8004"))
    host = os.getenv("DATA_PROCESSOR_HOST", "0.0.0.0")
    
    uvicorn.run("main:app", host=host, port=port, reload=True) 