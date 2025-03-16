from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List
import uuid
from enum import Enum


class JobStatus(Enum):
    """Estados posibles de un trabajo de cosecha."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class HarvestJob:
    """
    Entidad que representa un trabajo de cosecha de datos.
    
    Esta entidad contiene la información sobre un trabajo de cosecha,
    incluyendo su configuración, estado y resultados.
    """
    job_id: str
    source_type: str  # file, api, web
    config: Dict[str, Any]
    status: JobStatus
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    @staticmethod
    def create(source_type: str, config: Dict[str, Any], job_id: Optional[str] = None) -> 'HarvestJob':
        """
        Crea un nuevo trabajo de cosecha.
        
        Args:
            source_type: Tipo de fuente (file, api, web)
            config: Configuración para la cosecha
            job_id: ID opcional del trabajo (se genera uno si no se proporciona)
            
        Returns:
            Una nueva instancia de HarvestJob
        """
        return HarvestJob(
            job_id=job_id or str(uuid.uuid4()),
            source_type=source_type,
            config=config,
            status=JobStatus.PENDING
        )
    
    def start_processing(self) -> None:
        """Marca el trabajo como en procesamiento."""
        self.status = JobStatus.PROCESSING
        self.updated_at = datetime.utcnow()
    
    def complete(self, result: Dict[str, Any]) -> None:
        """
        Marca el trabajo como completado con un resultado.
        
        Args:
            result: Resultado del trabajo de cosecha
        """
        self.status = JobStatus.COMPLETED
        self.result = result
        self.updated_at = datetime.utcnow()
    
    def fail(self, error: str) -> None:
        """
        Marca el trabajo como fallido con un mensaje de error.
        
        Args:
            error: Mensaje de error
        """
        self.status = JobStatus.FAILED
        self.error = error
        self.updated_at = datetime.utcnow() 