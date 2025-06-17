from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List
import uuid
from enum import Enum


class JobStatus(Enum):
    """Estados posibles de un trabajo de integración."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class IntegrationJob:
    """
    Entidad que representa un trabajo de ejecución de integración.
    
    Un trabajo de integración es una instancia específica de ejecución
    de una integración de datos.
    """
    id: str
    integration_id: str
    status: JobStatus
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    records_processed: int = 0
    records_success: int = 0
    records_failed: int = 0
    logs: List[str] = field(default_factory=list)
    
    @staticmethod
    def create(integration_id: str, job_id: Optional[str] = None) -> 'IntegrationJob':
        """
        Crea un nuevo trabajo de integración.
        
        Args:
            integration_id: ID de la integración a ejecutar
            job_id: ID opcional del trabajo
            
        Returns:
            Una nueva instancia de IntegrationJob
        """
        return IntegrationJob(
            id=job_id or str(uuid.uuid4()),
            integration_id=integration_id,
            status=JobStatus.PENDING
        )
    
    def start(self) -> None:
        """Marca el trabajo como iniciado."""
        self.status = JobStatus.RUNNING
        self.started_at = datetime.utcnow()
    
    def complete(self, result: Dict[str, Any], records_processed: int = 0, 
                records_success: int = 0, records_failed: int = 0) -> None:
        """
        Marca el trabajo como completado.
        
        Args:
            result: Resultado del trabajo
            records_processed: Número de registros procesados
            records_success: Número de registros exitosos
            records_failed: Número de registros fallidos
        """
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.result = result
        self.records_processed = records_processed
        self.records_success = records_success
        self.records_failed = records_failed
    
    def fail(self, error_message: str) -> None:
        """
        Marca el trabajo como fallido.
        
        Args:
            error_message: Mensaje de error
        """
        self.status = JobStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.error_message = error_message
    
    def cancel(self) -> None:
        """Cancela el trabajo."""
        self.status = JobStatus.CANCELLED
        self.completed_at = datetime.utcnow()
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """Calcula la duración del trabajo en segundos."""
        if self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    @property
    def is_finished(self) -> bool:
        """Indica si el trabajo ha terminado (exitoso, fallido o cancelado)."""
        return self.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]
    
    def add_log(self, message: str) -> None:
        """
        Agrega un mensaje de log al trabajo.
        
        Args:
            message: Mensaje a agregar
        """
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        self.logs.append(f"[{timestamp}] {message}") 