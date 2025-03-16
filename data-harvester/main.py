from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import uuid
import json
import httpx
from dotenv import load_dotenv

# Import harvester modules
from harvester.file_harvester import FileHarvester
from harvester.api_harvester import APIHarvester
from harvester.web_harvester import WebHarvester
from utils.error_handler import ErrorHandler
from utils.file_utils import FileUtils

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Data Harvester Service",
    description="Service for harvesting data from various sources",
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

# Initialize harvesters
file_harvester = FileHarvester()
api_harvester = APIHarvester()
web_harvester = WebHarvester()

# Models
class HarvestRequest(BaseModel):
    source_type: str  # file, api, web
    config: Dict[str, Any]
    job_id: Optional[str] = None

class HarvestResponse(BaseModel):
    job_id: str
    status: str
    message: str
    data: Optional[Dict[str, Any]] = None

# Routes
@app.get("/")
async def root():
    return {"message": "Data Harvester Service is running"}

@app.post("/harvest", response_model=HarvestResponse)
async def harvest_data(request: HarvestRequest, background_tasks: BackgroundTasks):
    """Start a data harvesting job"""
    job_id = request.job_id or str(uuid.uuid4())
    
    # Start harvesting in background
    background_tasks.add_task(
        process_harvest_job,
        job_id=job_id,
        source_type=request.source_type,
        config=request.config
    )
    
    return {
        "job_id": job_id,
        "status": "started",
        "message": f"Harvesting job started for {request.source_type} source",
        "data": None
    }

@app.post("/upload", response_model=HarvestResponse)
async def upload_file(
    file: UploadFile = File(...),
    source_type: str = Form(...),
    job_id: Optional[str] = Form(None)
):
    """Upload a file for harvesting"""
    job_id = job_id or str(uuid.uuid4())
    
    # Save uploaded file
    file_info = await FileUtils.save_upload_file(file)
    
    # Create config for file harvester
    config = {
        "file_path": file_info["path"],
        "file_type": file_info["extension"].lower().replace(".", ""),
        "file_name": file_info["filename"]
    }
    
    # Notify orchestrator about the new file
    try:
        orchestrator_url = os.getenv("ORCHESTRATOR_URL", "http://localhost:8000")
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{orchestrator_url}/jobs/notify",
                json={
                    "job_id": job_id,
                    "service": "data-harvester",
                    "status": "uploaded",
                    "data": {
                        "file_info": file_info,
                        "config": config
                    }
                }
            )
    except Exception as e:
        print(f"Error notifying orchestrator: {str(e)}")
    
    return {
        "job_id": job_id,
        "status": "uploaded",
        "message": f"File {file.filename} uploaded successfully",
        "data": {
            "file_info": file_info,
            "config": config
        }
    }

@app.get("/jobs/{job_id}", response_model=HarvestResponse)
async def get_job_status(job_id: str):
    """Get the status of a harvesting job"""
    # In a real implementation, this would check a database or cache
    # For now, we'll just return a placeholder
    return {
        "job_id": job_id,
        "status": "unknown",
        "message": "Job status retrieval not implemented yet",
        "data": None
    }

@app.get("/sources")
async def get_available_sources():
    """Get all available data sources for harvesting"""
    return {
        "sources": [
            {
                "id": "file-csv",
                "name": "CSV File",
                "type": "file",
                "description": "Import data from CSV files"
            },
            {
                "id": "file-json",
                "name": "JSON File",
                "type": "file",
                "description": "Import data from JSON files"
            },
            {
                "id": "api-rest",
                "name": "REST API",
                "type": "api",
                "description": "Harvest data from REST APIs"
            },
            {
                "id": "web-scraper",
                "name": "Web Scraper",
                "type": "web",
                "description": "Harvest data from websites"
            }
        ]
    }

# Background task for processing harvest jobs
async def process_harvest_job(job_id: str, source_type: str, config: Dict[str, Any]):
    """Process a harvesting job in the background"""
    result = None
    status = "processing"
    error = None
    
    try:
        if source_type == "file":
            result = await file_harvester.harvest(config)
        elif source_type == "api":
            result = await api_harvester.harvest(config)
        elif source_type == "web":
            result = await web_harvester.harvest(config)
        else:
            raise ValueError(f"Unsupported source type: {source_type}")
        
        status = "completed"
    except Exception as e:
        status = "failed"
        error = str(e)
        print(f"Error processing harvest job {job_id}: {error}")
    
    # Notify orchestrator about job completion
    try:
        orchestrator_url = os.getenv("ORCHESTRATOR_URL", "http://localhost:8000")
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{orchestrator_url}/jobs/update",
                json={
                    "job_id": job_id,
                    "service": "data-harvester",
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