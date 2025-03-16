from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List


@dataclass
class DataColumn:
    """Representa una columna en un conjunto de datos cosechados."""
    name: str
    type: str  # string, number, boolean, etc.


@dataclass
class HarvestedData:
    """
    Entidad que representa los datos cosechados de una fuente.
    
    Esta entidad contiene los datos cosechados junto con metadatos
    sobre la fuente y la estructura de los datos.
    """
    source_type: str  # file, api, web
    source_identifier: str  # URL, ruta de archivo, etc.
    rows: List[Dict[str, Any]]
    columns: List[DataColumn]
    metadata: Dict[str, Any]
    harvested_at: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def row_count(self) -> int:
        """Número de filas en los datos cosechados."""
        return len(self.rows)
    
    @property
    def column_count(self) -> int:
        """Número de columnas en los datos cosechados."""
        return len(self.columns)
    
    def add_metadata(self, key: str, value: Any) -> None:
        """
        Añade un elemento de metadatos a los datos cosechados.
        
        Args:
            key: Clave del metadato
            value: Valor del metadato
        """
        self.metadata[key] = value 