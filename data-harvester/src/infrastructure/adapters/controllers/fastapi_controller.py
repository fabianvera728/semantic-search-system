from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import os
import uuid
import json

from src.application.use_cases.create_harvest_job_use_case import CreateHarvestJobUseCase
from src.application.use_cases.process_harvest_job_use_case import ProcessHarvestJobUseCase
from src.application.use_cases.get_job_status_use_case import GetJobStatusUseCase
from src.application.use_cases.get_available_sources_use_case import GetAvailableSourcesUseCase
from src.application.use_cases.upload_file_use_case import UploadFileUseCase
from src.domain.entities.harvest_job import JobStatus
from src.infrastructure.config.app_config import get_app_config


class HarvestRequest(BaseModel):
    """Modelo para solicitudes de cosecha."""
    source_type: str
    config: Dict[str, Any]
    source_id: Optional[str] = None
    job_id: Optional[str] = None


class HarvestResponse(BaseModel):
    """Modelo para respuestas de cosecha."""
    job_id: str
    status: str
    message: str
    data: Optional[Dict[str, Any]] = None


class FastAPIController:
    """
    Controlador que implementa la API REST utilizando FastAPI.
    
    Este controlador expone los endpoints para interactuar con el servicio
    de cosecha de datos.
    """
    
    def __init__(
        self,
        create_harvest_job_use_case: CreateHarvestJobUseCase,
        process_harvest_job_use_case: ProcessHarvestJobUseCase,
        get_job_status_use_case: GetJobStatusUseCase,
        get_available_sources_use_case: GetAvailableSourcesUseCase,
        upload_file_use_case: UploadFileUseCase
    ):
        """
        Inicializa el controlador con los casos de uso necesarios.
        
        Args:
            create_harvest_job_use_case: Caso de uso para crear trabajos
            process_harvest_job_use_case: Caso de uso para procesar trabajos
            get_job_status_use_case: Caso de uso para obtener estado de trabajos
            get_available_sources_use_case: Caso de uso para obtener fuentes
            upload_file_use_case: Caso de uso para subir archivos
        """
        self.create_harvest_job_use_case = create_harvest_job_use_case
        self.process_harvest_job_use_case = process_harvest_job_use_case
        self.get_job_status_use_case = get_job_status_use_case
        self.get_available_sources_use_case = get_available_sources_use_case
        self.upload_file_use_case = upload_file_use_case
        
        # Configuración de la aplicación
        self.config = get_app_config()
        
        # Crear aplicación FastAPI
        self.app = FastAPI(
            title="Data Harvester Service",
            description="Servicio para la cosecha de datos de diversas fuentes",
            version="1.0.0"
        )
        
        # Configurar CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"]
        )
        
        # Registrar rutas
        self._register_routes()
    
    def _register_routes(self):
        """Registra las rutas de la API."""
        
        @self.app.get("/")
        async def root():
            """Endpoint raíz para verificar que el servicio está funcionando."""
            return {"message": "Data Harvester Service is running"}
        
        @self.app.post("/harvest", response_model=HarvestResponse)
        async def harvest_data(request: HarvestRequest, background_tasks: BackgroundTasks):
            """
            Inicia un trabajo de cosecha de datos.
            
            Args:
                request: Solicitud de cosecha
                background_tasks: Tareas en segundo plano
                
            Returns:
                Respuesta con información del trabajo creado
            """
            try:
                # Crear trabajo de cosecha
                job = await self.create_harvest_job_use_case.execute(
                    source_type=request.source_type,
                    config=request.config,
                    source_id=request.source_id,
                    job_id=request.job_id
                )
                
                # Iniciar procesamiento en segundo plano
                background_tasks.add_task(self.process_harvest_job_use_case.execute, job.job_id)
                
                return {
                    "job_id": job.job_id,
                    "status": job.status.value,
                    "message": f"Trabajo de cosecha iniciado para fuente de tipo {request.source_type}",
                    "data": None
                }
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
        
        @self.app.post("/upload", response_model=HarvestResponse)
        async def upload_file(
            file: UploadFile = File(...),
            source_type: str = Form(...),
            job_id: Optional[str] = Form(None)
        ):
            """
            Sube un archivo para cosecha.
            
            Args:
                file: Archivo a subir
                source_type: Tipo de fuente
                job_id: ID opcional del trabajo
                
            Returns:
                Respuesta con información del archivo subido y el trabajo creado
            """
            try:
                # Determinar tipo de archivo
                file_name = file.filename
                file_extension = os.path.splitext(file_name)[1].lower().replace(".", "")
                
                # Guardar archivo
                upload_dir = self.config.upload_dir
                os.makedirs(upload_dir, exist_ok=True)
                
                file_path = os.path.join(upload_dir, f"{uuid.uuid4()}_{file_name}")
                
                with open(file_path, "wb") as f:
                    content = await file.read()
                    f.write(content)
                
                # Crear trabajo de cosecha
                result = await self.upload_file_use_case.execute(
                    file_path=file_path,
                    file_name=file_name,
                    file_type=file_extension,
                    job_id=job_id
                )
                
                return {
                    "job_id": result["job_id"],
                    "status": "pending",
                    "message": f"Archivo {file_name} subido correctamente",
                    "data": {
                        "file_info": result["file_info"],
                        "config": result["config"]
                    }
                }
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
        
        @self.app.get("/jobs/{job_id}", response_model=HarvestResponse)
        async def get_job_status(job_id: str):
            """
            Obtiene el estado de un trabajo de cosecha.
            
            Args:
                job_id: ID del trabajo
                
            Returns:
                Respuesta con información del trabajo
            """
            try:
                job = await self.get_job_status_use_case.execute(job_id)
                
                # Preparar datos de respuesta
                data = None
                if job.status == JobStatus.COMPLETED and job.result:
                    data = job.result
                
                return {
                    "job_id": job.job_id,
                    "status": job.status.value,
                    "message": f"Estado del trabajo: {job.status.value}",
                    "data": data
                }
            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
        
        @self.app.get("/sources")
        async def get_available_sources(source_type: Optional[str] = None):
            """
            Obtiene las fuentes de datos disponibles.
            
            Args:
                source_type: Tipo de fuente opcional para filtrar
                
            Returns:
                Lista de fuentes de datos disponibles
            """
            try:
                sources = self.get_available_sources_use_case.execute(source_type)
                
                # Convertir a formato de respuesta
                sources_data = []
                for source in sources:
                    sources_data.append({
                        "id": source.source_id,
                        "name": source.name,
                        "type": source.type,
                        "description": source.description,
                        "config_schema": source.config_schema
                    })
                
                return {"sources": sources_data}
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
    
    def get_app(self) -> FastAPI:
        """
        Obtiene la aplicación FastAPI configurada.
        
        Returns:
            La aplicación FastAPI
        """
        return self.app 