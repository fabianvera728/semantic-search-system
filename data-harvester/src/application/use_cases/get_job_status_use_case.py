from src.domain.entities.harvest_job import HarvestJob
from src.domain.services.harvester_service import HarvesterService


class GetJobStatusUseCase:
    """
    Caso de uso para obtener el estado de un trabajo de cosecha.
    
    Este caso de uso permite consultar el estado actual de un trabajo
    de cosecha existente.
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
        Ejecuta el caso de uso para obtener el estado de un trabajo.
        
        Args:
            job_id: ID del trabajo
            
        Returns:
            El trabajo de cosecha
            
        Raises:
            ValueError: Si el trabajo no existe
        """
        return await self.harvester_service.get_job_status(job_id) 