from typing import Dict, Any, Optional
import os

from src.domain.entities.harvest_job import HarvestJob
from src.domain.services.harvester_service import HarvesterService


class UploadFileUseCase:
    
    def __init__(self, harvester_service: HarvesterService, upload_dir: str):
        self.harvester_service = harvester_service
        self.upload_dir = upload_dir
        
        os.makedirs(self.upload_dir, exist_ok=True)
    
    async def execute(
        self,
        file_path: str,
        file_name: str,
        file_type: str,
        job_id: Optional[str] = None
    ) -> Dict[str, Any]:
        if file_type.lower() not in ["csv", "json"]:
            raise ValueError(f"Tipo de archivo no soportado: {file_type}")
        
        config = {
            "file_path": file_path,
            "file_type": file_type.lower(),
            "file_name": file_name
        }
        
        job = await self.harvester_service.create_harvest_job("file", config, job_id)
        
        return {
            "job_id": job.job_id,
            "file_info": {
                "filename": file_name,
                "path": file_path,
                "type": file_type
            },
            "config": config
        } 