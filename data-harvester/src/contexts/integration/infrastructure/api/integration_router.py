from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.contexts.integration.domain.entities import (
    DataIntegration, 
    IntegrationStatus, 
    IntegrationJob,
    JobStatus
)

integration_router = APIRouter()

# Almacenamiento en memoria (en producción sería una base de datos)
integrations_store: Dict[str, DataIntegration] = {}
jobs_store: Dict[str, IntegrationJob] = {}

# DTOs
class HarvestConfig(BaseModel):
    source_type: str  # file, api, web
    config: Dict[str, Any]
    column_mapping: Optional[Dict[str, str]] = {}  # mapeo de columnas fuente -> dataset

class CreateIntegrationRequest(BaseModel):
    name: str
    description: str
    dataset_id: str
    harvest_config: HarvestConfig
    processing_config: Optional[Dict[str, Any]] = None
    is_active: bool = True

class UpdateIntegrationRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    dataset_id: Optional[str] = None
    harvest_config: Optional[HarvestConfig] = None
    processing_config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class IntegrationResponse(BaseModel):
    id: str
    name: str
    description: str
    dataset_id: str
    dataset_name: Optional[str] = None
    harvest_config: HarvestConfig
    processing_config: Optional[Dict[str, Any]]
    status: str
    created_at: datetime
    updated_at: datetime
    last_run: Optional[datetime]
    created_by: Optional[str]

class JobResponse(BaseModel):
    id: str
    integration_id: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    result: Optional[Dict[str, Any]]
    error_message: Optional[str]
    records_processed: int
    records_success: int
    records_failed: int
    duration_seconds: Optional[float]
    logs: List[str] = []

# Endpoints de Integraciones
@integration_router.get("/integrations", response_model=List[IntegrationResponse])
async def get_integrations():
    """Obtener todas las integraciones."""
    return [
        IntegrationResponse(
            id=integration.id,
            name=integration.name,
            description=integration.description,
            dataset_id=integration.dataset_id,
            dataset_name=f"Dataset {integration.dataset_id[:8]}",  # Placeholder
            harvest_config=HarvestConfig(
                source_type=integration.harvest_config["source_type"],
                config=integration.harvest_config["config"],
                column_mapping=integration.harvest_config.get("column_mapping", {})
            ),
            processing_config=integration.processing_config,
            status=integration.status.value,
            created_at=integration.created_at,
            updated_at=integration.updated_at,
            last_run=integration.last_run,
            created_by=integration.created_by
        )
        for integration in integrations_store.values()
    ]

@integration_router.post("/integrations", response_model=IntegrationResponse)
async def create_integration(request: CreateIntegrationRequest):
    """Crear una nueva integración."""
    # Convertir harvest_config a dict
    harvest_config_dict = {
        "source_type": request.harvest_config.source_type,
        "config": request.harvest_config.config,
        "column_mapping": request.harvest_config.column_mapping or {}
    }
    
    integration = DataIntegration.create(
        name=request.name,
        description=request.description,
        dataset_id=request.dataset_id,
        harvest_config=harvest_config_dict,
        processing_config=request.processing_config,
        is_active=request.is_active
    )
    
    integrations_store[integration.id] = integration
    
    return IntegrationResponse(
        id=integration.id,
        name=integration.name,
        description=integration.description,
        dataset_id=integration.dataset_id,
        dataset_name=f"Dataset {integration.dataset_id[:8]}",  # Placeholder
        harvest_config=HarvestConfig(
            source_type=integration.harvest_config["source_type"],
            config=integration.harvest_config["config"],
            column_mapping=integration.harvest_config.get("column_mapping", {})
        ),
        processing_config=integration.processing_config,
        status=integration.status.value,
        created_at=integration.created_at,
        updated_at=integration.updated_at,
        last_run=integration.last_run,
        created_by=integration.created_by
    )

@integration_router.get("/integrations/{integration_id}", response_model=IntegrationResponse)
async def get_integration(integration_id: str):
    """Obtener una integración específica."""
    if integration_id not in integrations_store:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    integration = integrations_store[integration_id]
    return IntegrationResponse(
        id=integration.id,
        name=integration.name,
        description=integration.description,
        dataset_id=integration.dataset_id,
        dataset_name=f"Dataset {integration.dataset_id[:8]}",  # Placeholder
        harvest_config=HarvestConfig(
            source_type=integration.harvest_config["source_type"],
            config=integration.harvest_config["config"],
            column_mapping=integration.harvest_config.get("column_mapping", {})
        ),
        processing_config=integration.processing_config,
        status=integration.status.value,
        created_at=integration.created_at,
        updated_at=integration.updated_at,
        last_run=integration.last_run,
        created_by=integration.created_by
    )

@integration_router.put("/integrations/{integration_id}", response_model=IntegrationResponse)
async def update_integration(integration_id: str, request: UpdateIntegrationRequest):
    """Actualizar una integración."""
    if integration_id not in integrations_store:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    integration = integrations_store[integration_id]
    
    if request.name is not None:
        integration.name = request.name
    if request.description is not None:
        integration.description = request.description
    if request.dataset_id is not None:
        integration.dataset_id = request.dataset_id
    
    if request.harvest_config is not None or request.processing_config is not None:
        harvest_config = integration.harvest_config
        if request.harvest_config is not None:
            harvest_config = {
                "source_type": request.harvest_config.source_type,
                "config": request.harvest_config.config,
                "column_mapping": request.harvest_config.column_mapping or {}
            }
        integration.update_config(harvest_config, request.processing_config)
    
    if request.is_active is not None:
        if request.is_active:
            integration.activate()
        else:
            integration.deactivate()
    
    return IntegrationResponse(
        id=integration.id,
        name=integration.name,
        description=integration.description,
        dataset_id=integration.dataset_id,
        dataset_name=f"Dataset {integration.dataset_id[:8]}",  # Placeholder
        harvest_config=HarvestConfig(
            source_type=integration.harvest_config["source_type"],
            config=integration.harvest_config["config"],
            column_mapping=integration.harvest_config.get("column_mapping", {})
        ),
        processing_config=integration.processing_config,
        status=integration.status.value,
        created_at=integration.created_at,
        updated_at=integration.updated_at,
        last_run=integration.last_run,
        created_by=integration.created_by
    )

@integration_router.delete("/integrations/{integration_id}")
async def delete_integration(integration_id: str):
    """Eliminar una integración."""
    if integration_id not in integrations_store:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    del integrations_store[integration_id]
    return {"message": "Integration deleted successfully"}

@integration_router.post("/integrations/{integration_id}/run", response_model=JobResponse)
async def run_integration(integration_id: str, background_tasks: BackgroundTasks):
    """Ejecutar una integración."""
    if integration_id not in integrations_store:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    integration = integrations_store[integration_id]
    
    if integration.status != IntegrationStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Integration is not active")
    
    job = IntegrationJob.create(integration_id)
    jobs_store[job.id] = job
    
    # Ejecutar en background
    background_tasks.add_task(execute_integration_job, job.id)
    
    return JobResponse(
        id=job.id,
        integration_id=job.integration_id,
        status=job.status.value,
        started_at=job.started_at,
        completed_at=job.completed_at,
        result=job.result,
        error_message=job.error_message,
        records_processed=job.records_processed,
        records_success=job.records_success,
        records_failed=job.records_failed,
        duration_seconds=job.duration_seconds,
        logs=job.logs
    )

# Endpoints de Jobs
@integration_router.get("/jobs", response_model=List[JobResponse])
async def get_jobs():
    """Obtener todos los trabajos de integración."""
    return [
        JobResponse(
            id=job.id,
            integration_id=job.integration_id,
            status=job.status.value,
            started_at=job.started_at,
            completed_at=job.completed_at,
            result=job.result,
            error_message=job.error_message,
            records_processed=job.records_processed,
            records_success=job.records_success,
            records_failed=job.records_failed,
            duration_seconds=job.duration_seconds,
            logs=job.logs
        )
        for job in jobs_store.values()
    ]

@integration_router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str):
    """Obtener un trabajo específico."""
    if job_id not in jobs_store:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs_store[job_id]
    return JobResponse(
        id=job.id,
        integration_id=job.integration_id,
        status=job.status.value,
        started_at=job.started_at,
        completed_at=job.completed_at,
        result=job.result,
        error_message=job.error_message,
        records_processed=job.records_processed,
        records_success=job.records_success,
        records_failed=job.records_failed,
        duration_seconds=job.duration_seconds,
        logs=job.logs
    )

async def execute_integration_job(job_id: str):
    """Ejecuta un trabajo de integración en background."""
    if job_id not in jobs_store:
        return
    
    job = jobs_store[job_id]
    integration = integrations_store.get(job.integration_id)
    
    if not integration:
        job.fail("Integration not found")
        return
    
    try:
        job.start()
        job.add_log(f"Iniciando ejecución de integración: {integration.name}")
        
        # Usar el servicio de ejecución de integraciones
        from ..services.integration_execution_service import IntegrationExecutionService
        execution_service = IntegrationExecutionService()
        
        result = await execution_service.execute_integration(integration, job)
        
        # Calcular estadísticas finales
        storage_info = result.get("storage_info", {})
        records_processed = storage_info.get("total_rows", 0)
        records_success = storage_info.get("rows_added", 0)
        records_failed = storage_info.get("rows_failed", 0)
        
        job.complete(result, records_processed, records_success, records_failed)
        integration.update_last_run()
        
        job.add_log("Integración completada exitosamente")
        
    except Exception as e:
        job.fail(str(e))
        integration.mark_error()
        job.add_log(f"Error en la integración: {str(e)}") 