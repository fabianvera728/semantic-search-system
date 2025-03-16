from typing import Dict, Any, Optional

from src.domain.entities.harvest_job import HarvestJob
from src.domain.services.harvester_service import HarvesterService
from src.domain.services.data_source_service import DataSourceService


class CreateHarvestJobUseCase:
    """
    Caso de uso para crear un nuevo trabajo de cosecha.
    
    Este caso de uso coordina la validación de la configuración
    y la creación del trabajo de cosecha.
    """
    
    def __init__(self, harvester_service: HarvesterService, data_source_service: DataSourceService):
        """
        Inicializa el caso de uso con los servicios necesarios.
        
        Args:
            harvester_service: Servicio para gestionar trabajos de cosecha
            data_source_service: Servicio para gestionar fuentes de datos
        """
        self.harvester_service = harvester_service
        self.data_source_service = data_source_service
    
    async def execute(
        self,
        source_type: str,
        config: Dict[str, Any],
        source_id: Optional[str] = None,
        job_id: Optional[str] = None
    ) -> HarvestJob:
        """
        Ejecuta el caso de uso para crear un trabajo de cosecha.
        
        Args:
            source_type: Tipo de fuente (file, api, web)
            config: Configuración para la cosecha
            source_id: ID opcional de la fuente para validación
            job_id: ID opcional del trabajo
            
        Returns:
            El trabajo de cosecha creado
            
        Raises:
            ValueError: Si el tipo de fuente no es válido o la configuración es inválida
        """
        # Validar tipo de fuente
        if source_type not in ["file", "api", "web"]:
            raise ValueError(f"Tipo de fuente no válido: {source_type}")
        
        # Validar configuración si se proporciona un ID de fuente
        if source_id:
            self.data_source_service.validate_config(source_id, config)
        
        # Crear trabajo de cosecha
        job = await self.harvester_service.create_harvest_job(source_type, config, job_id)
        
        return job 