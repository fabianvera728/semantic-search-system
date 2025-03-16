from typing import Dict, Any, Optional

from src.domain.entities.harvest_job import HarvestJob, JobStatus
from src.domain.entities.harvested_data import HarvestedData
from src.domain.ports.harvester_port import HarvesterPort
from src.domain.ports.harvester_repository_port import HarvesterRepositoryPort
from src.domain.ports.notification_port import NotificationPort


class HarvesterService:
    """
    Servicio del dominio que implementa la lógica de negocio para la cosecha de datos.
    
    Este servicio coordina el proceso de cosecha utilizando los puertos
    definidos en el dominio.
    """
    
    def __init__(
        self,
        file_harvester: HarvesterPort,
        api_harvester: HarvesterPort,
        web_harvester: HarvesterPort,
        repository: HarvesterRepositoryPort,
        notifier: NotificationPort
    ):
        """
        Inicializa el servicio con los puertos necesarios.
        
        Args:
            file_harvester: Implementación del puerto para cosechar archivos
            api_harvester: Implementación del puerto para cosechar APIs
            web_harvester: Implementación del puerto para cosechar sitios web
            repository: Implementación del puerto para el repositorio de trabajos
            notifier: Implementación del puerto para notificaciones
        """
        self.harvesters = {
            "file": file_harvester,
            "api": api_harvester,
            "web": web_harvester
        }
        self.repository = repository
        self.notifier = notifier
    
    async def create_harvest_job(self, source_type: str, config: Dict[str, Any], job_id: Optional[str] = None) -> HarvestJob:
        """
        Crea un nuevo trabajo de cosecha.
        
        Args:
            source_type: Tipo de fuente (file, api, web)
            config: Configuración para la cosecha
            job_id: ID opcional del trabajo
            
        Returns:
            El trabajo de cosecha creado
            
        Raises:
            ValueError: Si el tipo de fuente no es válido
        """
        if source_type not in self.harvesters:
            raise ValueError(f"Tipo de fuente no válido: {source_type}")
        
        job = HarvestJob.create(source_type, config, job_id)
        saved_job = await self.repository.save(job)
        await self.notifier.notify_job_created(saved_job)
        
        return saved_job
    
    async def process_harvest_job(self, job_id: str) -> HarvestJob:
        """
        Procesa un trabajo de cosecha existente.
        
        Args:
            job_id: ID del trabajo a procesar
            
        Returns:
            El trabajo procesado
            
        Raises:
            ValueError: Si el trabajo no existe o el tipo de fuente no es válido
        """
        job = await self.repository.find_by_id(job_id)
        if not job:
            raise ValueError(f"Trabajo no encontrado: {job_id}")
        
        if job.source_type not in self.harvesters:
            raise ValueError(f"Tipo de fuente no válido: {job.source_type}")
        
        # Actualizar estado a procesando
        job.start_processing()
        await self.repository.update(job)
        await self.notifier.notify_job_started(job)
        
        try:
            # Realizar la cosecha
            harvester = self.harvesters[job.source_type]
            harvested_data = await harvester.harvest(job.config)
            
            # Actualizar trabajo con resultado exitoso
            result = {
                "rows": harvested_data.rows,
                "columns": [{"name": col.name, "type": col.type} for col in harvested_data.columns],
                "metadata": harvested_data.metadata,
                "source_type": harvested_data.source_type,
                "source_identifier": harvested_data.source_identifier,
                "row_count": harvested_data.row_count,
                "column_count": harvested_data.column_count,
                "harvested_at": harvested_data.harvested_at.isoformat()
            }
            
            job.complete(result)
            await self.repository.update(job)
            await self.notifier.notify_job_completed(job, result)
            
        except Exception as e:
            # Actualizar trabajo con error
            error_message = str(e)
            job.fail(error_message)
            await self.repository.update(job)
            await self.notifier.notify_job_failed(job, error_message)
        
        return job
    
    async def get_job_status(self, job_id: str) -> HarvestJob:
        """
        Obtiene el estado actual de un trabajo de cosecha.
        
        Args:
            job_id: ID del trabajo
            
        Returns:
            El trabajo de cosecha
            
        Raises:
            ValueError: Si el trabajo no existe
        """
        job = await self.repository.find_by_id(job_id)
        if not job:
            raise ValueError(f"Trabajo no encontrado: {job_id}")
        
        return job
    
    async def get_all_jobs(self) -> list[HarvestJob]:
        """
        Obtiene todos los trabajos de cosecha.
        
        Returns:
            Lista de todos los trabajos
        """
        return await self.repository.find_all() 