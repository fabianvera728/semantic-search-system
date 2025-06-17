from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uuid

from src.contexts.harvest.domain.entities import HarvestJob, JobStatus
from src.contexts.harvest.infrastructure.harvesters.file_harvester import FileHarvester
from src.contexts.harvest.infrastructure.harvesters.api_harvester import APIHarvester
from src.contexts.harvest.infrastructure.harvesters.web_harvester import WebHarvester

harvest_router = APIRouter()

# Inicializar harvesters
file_harvester = FileHarvester()
api_harvester = APIHarvester()
web_harvester = WebHarvester()

# DTOs
class HarvestRequest(BaseModel):
    source_type: str  # file, api, web
    config: Dict[str, Any]
    job_id: Optional[str] = None

class HarvestResponse(BaseModel):
    job_id: str
    status: str
    message: str
    data: Optional[Dict[str, Any]] = None

class DataSource(BaseModel):
    id: str
    name: str
    type: str
    description: str

@harvest_router.post("/harvest", response_model=HarvestResponse)
async def harvest_data(request: HarvestRequest, background_tasks: BackgroundTasks):
    """Iniciar cosecha de datos."""
    job_id = request.job_id or str(uuid.uuid4())
    
    background_tasks.add_task(
        process_harvest_job,
        job_id=job_id,
        source_type=request.source_type,
        config=request.config
    )
    
    return HarvestResponse(
        job_id=job_id,
        status="started",
        message=f"Harvesting job started for {request.source_type} source",
        data=None
    )

@harvest_router.post("/upload", response_model=HarvestResponse)
async def upload_file(
    file: UploadFile = File(...),
    source_type: str = Form(...),
    job_id: Optional[str] = Form(None)
):
    """Subir archivo para cosecha."""
    job_id = job_id or str(uuid.uuid4())
    
    # TODO: Implementar guardado de archivo
    file_info = {
        "filename": file.filename,
        "content_type": file.content_type,
        "size": file.size
    }
    
    return HarvestResponse(
        job_id=job_id,
        status="uploaded",
        message=f"File {file.filename} uploaded successfully",
        data={"file_info": file_info}
    )

@harvest_router.get("/sources")
async def get_available_sources():
    """Obtener fuentes de datos disponibles."""
    return {
        "sources": [
            DataSource(
                id="file-csv",
                name="CSV File",
                type="file",
                description="Import data from CSV files"
            ),
            DataSource(
                id="file-json",
                name="JSON File", 
                type="file",
                description="Import data from JSON files"
            ),
            DataSource(
                id="api-rest",
                name="REST API",
                type="api", 
                description="Harvest data from REST APIs"
            ),
            DataSource(
                id="web-scraper",
                name="Web Scraper",
                type="web",
                description="Harvest data from websites"
            )
        ]
    }

async def process_harvest_job(job_id: str, source_type: str, config: Dict[str, Any]):
    """Procesar trabajo de cosecha."""
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
    
    # TODO: Notificar al orchestrator si es necesario
    print(f"Job {job_id} completed with status: {status}") 