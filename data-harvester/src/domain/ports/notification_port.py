from abc import ABC, abstractmethod
from typing import Dict, Any

from src.domain.entities.harvest_job import HarvestJob


class NotificationPort(ABC):
    """
    Puerto que define la interfaz para notificar sobre los trabajos de cosecha.
    
    Esta interfaz debe ser implementada por todos los adaptadores
    que envían notificaciones sobre el estado de los trabajos de cosecha.
    """
    
    @abstractmethod
    async def notify_job_created(self, job: HarvestJob) -> None:
        """
        Notifica que se ha creado un nuevo trabajo de cosecha.
        
        Args:
            job: El trabajo de cosecha creado
        """
        pass
    
    @abstractmethod
    async def notify_job_started(self, job: HarvestJob) -> None:
        """
        Notifica que ha comenzado un trabajo de cosecha.
        
        Args:
            job: El trabajo de cosecha iniciado
        """
        pass
    
    @abstractmethod
    async def notify_job_completed(self, job: HarvestJob, result: Dict[str, Any]) -> None:
        """
        Notifica que se ha completado un trabajo de cosecha.
        
        Args:
            job: El trabajo de cosecha completado
            result: El resultado del trabajo
        """
        pass
    
    @abstractmethod
    async def notify_job_failed(self, job: HarvestJob, error: str) -> None:
        """
        Notifica que ha fallado un trabajo de cosecha.
        
        Args:
            job: El trabajo de cosecha fallido
            error: El mensaje de error
        """
        pass 