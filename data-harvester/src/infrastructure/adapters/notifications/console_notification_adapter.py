import logging
from typing import Dict, Any

from src.domain.entities.harvest_job import HarvestJob
from src.domain.ports.notification_port import NotificationPort


class ConsoleNotificationAdapter(NotificationPort):
    """
    Adaptador que implementa el puerto de notificaciones utilizando la consola.
    
    Este adaptador simplemente registra las notificaciones en el log del sistema.
    """
    
    def __init__(self):
        """Inicializa el adaptador con un logger."""
        self.logger = logging.getLogger(__name__)
    
    async def notify_job_created(self, job: HarvestJob) -> None:
        """
        Notifica que se ha creado un trabajo de cosecha.
        
        Args:
            job: El trabajo creado
        """
        self.logger.info(f"Trabajo de cosecha creado: {job.job_id} (tipo: {job.source_type})")
    
    async def notify_job_started(self, job: HarvestJob) -> None:
        """
        Notifica que ha comenzado el procesamiento de un trabajo.
        
        Args:
            job: El trabajo que ha comenzado
        """
        self.logger.info(f"Procesamiento iniciado para trabajo: {job.job_id}")
    
    async def notify_job_completed(self, job: HarvestJob, result: Dict[str, Any]) -> None:
        """
        Notifica que se ha completado un trabajo con éxito.
        
        Args:
            job: El trabajo completado
            result: El resultado del trabajo
        """
        row_count = result.get("row_count", 0)
        column_count = result.get("column_count", 0)
        self.logger.info(
            f"Trabajo completado: {job.job_id} - "
            f"Filas: {row_count}, Columnas: {column_count}"
        )
    
    async def notify_job_failed(self, job: HarvestJob, error: str) -> None:
        """
        Notifica que un trabajo ha fallado.
        
        Args:
            job: El trabajo fallido
            error: Mensaje de error
        """
        self.logger.error(f"Error en trabajo {job.job_id}: {error}")
    
    async def notify_progress(self, job_id: str, progress: float, message: str) -> None:
        """
        Notifica el progreso de un trabajo.
        
        Args:
            job_id: ID del trabajo
            progress: Porcentaje de progreso (0-100)
            message: Mensaje descriptivo
        """
        self.logger.info(f"Progreso del trabajo {job_id}: {progress:.1f}% - {message}") 