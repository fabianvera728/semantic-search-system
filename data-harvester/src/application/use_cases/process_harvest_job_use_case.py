from src.domain.entities.harvest_job import HarvestJob
from src.domain.services.harvester_service import HarvesterService


class ProcessHarvestJobUseCase:
    """
    Caso de uso para procesar un trabajo de cosecha existente.
    
    Este caso de uso coordina el procesamiento de un trabajo de cosecha,
    delegando la lógica al servicio del dominio.
    """
    
    def __init__(self, harvester_service: HarvesterService):
        """
        Inicializa el caso de uso con los servicios necesarios.
        
        Args:
            harvester_service: Servicio para gestionar trabajos de cosecha
        """
        self.harvester_service = harvester_service
    
    async def execute(self, job_id: str) -> HarvestJob:
        """
        Ejecuta el caso de uso para procesar un trabajo de cosecha.
        
        Args:
            job_id: ID del trabajo a procesar
            
        Returns:
            El trabajo procesado
            
        Raises:
            ValueError: Si el trabajo no existe
        """
        return await self.harvester_service.process_harvest_job(job_id) 