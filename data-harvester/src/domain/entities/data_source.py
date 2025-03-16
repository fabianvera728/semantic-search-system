from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List
import uuid


@dataclass
class DataSource:
    """
    Entidad que representa una fuente de datos.
    
    Esta entidad es inmutable y contiene la información básica de una fuente de datos
    que puede ser cosechada por el sistema.
    """
    source_id: str
    name: str
    type: str  # file, api, web
    description: str
    config_schema: Dict[str, str]
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    @staticmethod
    def create(name: str, type: str, description: str, config_schema: Dict[str, str]) -> 'DataSource':
        """
        Crea una nueva instancia de DataSource con un ID generado.
        
        Args:
            name: Nombre de la fuente de datos
            type: Tipo de fuente (file, api, web)
            description: Descripción de la fuente
            config_schema: Esquema de configuración requerido
            
        Returns:
            Una nueva instancia de DataSource
        """
        return DataSource(
            source_id=str(uuid.uuid4()),
            name=name,
            type=type,
            description=description,
            config_schema=config_schema
        ) 