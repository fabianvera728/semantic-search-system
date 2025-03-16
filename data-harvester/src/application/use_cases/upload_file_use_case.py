from typing import Dict, Any, Optional
import os

from src.domain.entities.harvest_job import HarvestJob
from src.domain.services.harvester_service import HarvesterService


class UploadFileUseCase:
    """
    Caso de uso para subir un archivo y crear un trabajo de cosecha.
    
    Este caso de uso coordina la subida de un archivo y la creación
    de un trabajo de cosecha para procesarlo.
    """
    
    def __init__(self, harvester_service: HarvesterService, upload_dir: str):
        """
        Inicializa el caso de uso con los servicios necesarios.
        
        Args:
            harvester_service: Servicio para gestionar trabajos de cosecha
            upload_dir: Directorio para guardar los archivos subidos
        """
        self.harvester_service = harvester_service
        self.upload_dir = upload_dir
        
        # Asegurar que el directorio de subida exista
        os.makedirs(self.upload_dir, exist_ok=True)
    
    async def execute(
        self,
        file_path: str,
        file_name: str,
        file_type: str,
        job_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Ejecuta el caso de uso para subir un archivo y crear un trabajo.
        
        Args:
            file_path: Ruta del archivo guardado
            file_name: Nombre original del archivo
            file_type: Tipo de archivo (csv, json, etc.)
            job_id: ID opcional del trabajo
            
        Returns:
            Información sobre el archivo subido y el trabajo creado
            
        Raises:
            ValueError: Si el tipo de archivo no es válido
        """
        # Validar tipo de archivo
        if file_type.lower() not in ["csv", "json"]:
            raise ValueError(f"Tipo de archivo no soportado: {file_type}")
        
        # Crear configuración para el cosechador de archivos
        config = {
            "file_path": file_path,
            "file_type": file_type.lower(),
            "file_name": file_name
        }
        
        # Crear trabajo de cosecha
        job = await self.harvester_service.create_harvest_job("file", config, job_id)
        
        # Preparar respuesta
        return {
            "job_id": job.job_id,
            "file_info": {
                "filename": file_name,
                "path": file_path,
                "type": file_type
            },
            "config": config
        } 