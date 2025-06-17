from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List
import uuid
from enum import Enum


class IntegrationStatus(Enum):
    """Estados posibles de una integración."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"


# IntegrationType ya no se usa - el tipo se obtiene de harvest_config["source_type"]


@dataclass
class DataIntegration:
    """
    Entidad que representa una integración de datos.
    
    Una integración define cómo obtener datos de una fuente externa
    y cómo procesarlos antes de almacenarlos.
    """
    id: str
    name: str
    description: str
    dataset_id: str
    harvest_config: Dict[str, Any]  # Incluye source_type y config
    processing_config: Optional[Dict[str, Any]]
    status: IntegrationStatus
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_run: Optional[datetime] = None
    created_by: Optional[str] = None
    
    @staticmethod
    def create(
        name: str,
        description: str,
        dataset_id: str,
        harvest_config: Dict[str, Any],
        processing_config: Optional[Dict[str, Any]] = None,
        is_active: bool = True,
        created_by: Optional[str] = None,
        integration_id: Optional[str] = None
    ) -> 'DataIntegration':
        """
        Crea una nueva integración de datos.
        
        Args:
            name: Nombre de la integración
            description: Descripción de la integración
            dataset_id: ID del dataset destino
            harvest_config: Configuración de cosecha (source_type y config)
            processing_config: Configuración de procesamiento
            is_active: Si la integración está activa
            created_by: Usuario que crea la integración
            integration_id: ID opcional de la integración
            
        Returns:
            Una nueva instancia de DataIntegration
        """
        return DataIntegration(
            id=integration_id or str(uuid.uuid4()),
            name=name,
            description=description,
            dataset_id=dataset_id,
            harvest_config=harvest_config,
            processing_config=processing_config,
            status=IntegrationStatus.ACTIVE if is_active else IntegrationStatus.INACTIVE,
            created_by=created_by
        )
    
    def update_config(self, harvest_config: Dict[str, Any], processing_config: Optional[Dict[str, Any]] = None) -> None:
        """
        Actualiza la configuración de la integración.
        
        Args:
            harvest_config: Nueva configuración de cosecha
            processing_config: Nueva configuración de procesamiento
        """
        self.harvest_config = harvest_config
        if processing_config is not None:
            self.processing_config = processing_config
        self.updated_at = datetime.utcnow()
    
    def activate(self) -> None:
        """Activa la integración."""
        self.status = IntegrationStatus.ACTIVE
        self.updated_at = datetime.utcnow()
    
    def deactivate(self) -> None:
        """Desactiva la integración."""
        self.status = IntegrationStatus.INACTIVE
        self.updated_at = datetime.utcnow()
    
    def mark_error(self) -> None:
        """Marca la integración como con error."""
        self.status = IntegrationStatus.ERROR
        self.updated_at = datetime.utcnow()
    
    def update_last_run(self) -> None:
        """Actualiza la fecha de última ejecución."""
        self.last_run = datetime.utcnow()
        self.updated_at = datetime.utcnow() 