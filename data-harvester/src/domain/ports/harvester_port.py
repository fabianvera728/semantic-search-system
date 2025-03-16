from abc import ABC, abstractmethod
from typing import Dict, Any

from src.domain.entities.harvested_data import HarvestedData


class HarvesterPort(ABC):
    """
    Puerto que define la interfaz para los cosechadores de datos.
    
    Esta interfaz debe ser implementada por todos los adaptadores
    que realizan la cosecha de datos de diferentes fuentes.
    """
    
    @abstractmethod
    async def harvest(self, config: Dict[str, Any]) -> HarvestedData:
        """
        Cosecha datos de una fuente según la configuración proporcionada.
        
        Args:
            config: Configuración específica para la cosecha
            
        Returns:
            Los datos cosechados
            
        Raises:
            ValueError: Si la configuración es inválida o la cosecha falla
        """
        pass 