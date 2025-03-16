from abc import ABC, abstractmethod
from typing import List, Optional

from src.domain.entities.harvest_job import HarvestJob


class HarvesterRepositoryPort(ABC):
    """
    Puerto que define la interfaz para el repositorio de trabajos de cosecha.
    
    Esta interfaz debe ser implementada por todos los adaptadores
    que proporcionan acceso a la persistencia de los trabajos de cosecha.
    """
    
    @abstractmethod
    async def save(self, job: HarvestJob) -> HarvestJob:
        """
        Guarda un trabajo de cosecha en el repositorio.
        
        Args:
            job: El trabajo de cosecha a guardar
            
        Returns:
            El trabajo guardado (posiblemente con ID actualizado)
        """
        pass
    
    @abstractmethod
    async def find_by_id(self, job_id: str) -> Optional[HarvestJob]:
        """
        Busca un trabajo de cosecha por su ID.
        
        Args:
            job_id: ID del trabajo a buscar
            
        Returns:
            El trabajo encontrado o None si no existe
        """
        pass
    
    @abstractmethod
    async def find_all(self) -> List[HarvestJob]:
        """
        Recupera todos los trabajos de cosecha.
        
        Returns:
            Lista de todos los trabajos de cosecha
        """
        pass
    
    @abstractmethod
    async def update(self, job: HarvestJob) -> HarvestJob:
        """
        Actualiza un trabajo de cosecha existente.
        
        Args:
            job: El trabajo con los datos actualizados
            
        Returns:
            El trabajo actualizado
            
        Raises:
            ValueError: Si el trabajo no existe
        """
        pass
    
    @abstractmethod
    async def delete(self, job_id: str) -> None:
        """
        Elimina un trabajo de cosecha.
        
        Args:
            job_id: ID del trabajo a eliminar
            
        Raises:
            ValueError: Si el trabajo no existe
        """
        pass 