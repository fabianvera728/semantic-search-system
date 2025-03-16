from typing import List, Optional

from src.domain.entities.data_source import DataSource
from src.domain.services.data_source_service import DataSourceService


class GetAvailableSourcesUseCase:
    """
    Caso de uso para obtener las fuentes de datos disponibles.
    
    Este caso de uso permite consultar las fuentes de datos
    que pueden ser utilizadas para la cosecha.
    """
    
    def __init__(self, data_source_service: DataSourceService):
        """
        Inicializa el caso de uso con los servicios necesarios.
        
        Args:
            data_source_service: Servicio para gestionar fuentes de datos
        """
        self.data_source_service = data_source_service
    
    def execute(self, source_type: Optional[str] = None) -> List[DataSource]:
        """
        Ejecuta el caso de uso para obtener las fuentes disponibles.
        
        Args:
            source_type: Tipo de fuente opcional para filtrar (file, api, web)
            
        Returns:
            Lista de fuentes de datos disponibles
        """
        if source_type:
            return self.data_source_service.get_sources_by_type(source_type)
        else:
            return self.data_source_service.get_all_sources() 