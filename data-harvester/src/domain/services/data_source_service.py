from typing import List, Dict, Any

from src.domain.entities.data_source import DataSource


class DataSourceService:
    """
    Servicio del dominio que gestiona las fuentes de datos disponibles.
    
    Este servicio proporciona información sobre las fuentes de datos
    que pueden ser utilizadas para la cosecha.
    """
    
    def __init__(self):
        """Inicializa el servicio con las fuentes de datos predefinidas."""
        self.sources = [
            DataSource.create(
                name="CSV File",
                type="file",
                description="Import data from CSV files",
                config_schema={
                    "file_path": "string",
                    "delimiter": "string",
                    "has_header": "boolean"
                }
            ),
            DataSource.create(
                name="JSON File",
                type="file",
                description="Import data from JSON files",
                config_schema={
                    "file_path": "string",
                    "root_path": "string"
                }
            ),
            DataSource.create(
                name="REST API",
                type="api",
                description="Harvest data from REST APIs",
                config_schema={
                    "url": "string",
                    "method": "string",
                    "headers": "object",
                    "params": "object",
                    "data": "object",
                    "auth": "object",
                    "root_path": "string"
                }
            ),
            DataSource.create(
                name="Web Scraper",
                type="web",
                description="Harvest data from websites",
                config_schema={
                    "urls": "array",
                    "selectors": "object"
                }
            )
        ]
    
    def get_all_sources(self) -> List[DataSource]:
        """
        Obtiene todas las fuentes de datos disponibles.
        
        Returns:
            Lista de todas las fuentes de datos
        """
        return self.sources
    
    def get_sources_by_type(self, source_type: str) -> List[DataSource]:
        """
        Obtiene las fuentes de datos de un tipo específico.
        
        Args:
            source_type: Tipo de fuente (file, api, web)
            
        Returns:
            Lista de fuentes de datos del tipo especificado
        """
        return [source for source in self.sources if source.type == source_type]
    
    def get_source_by_id(self, source_id: str) -> DataSource:
        """
        Obtiene una fuente de datos por su ID.
        
        Args:
            source_id: ID de la fuente
            
        Returns:
            La fuente de datos
            
        Raises:
            ValueError: Si la fuente no existe
        """
        for source in self.sources:
            if source.source_id == source_id:
                return source
        
        raise ValueError(f"Fuente de datos no encontrada: {source_id}")
    
    def validate_config(self, source_id: str, config: Dict[str, Any]) -> bool:
        """
        Valida que una configuración cumpla con el esquema de una fuente.
        
        Args:
            source_id: ID de la fuente
            config: Configuración a validar
            
        Returns:
            True si la configuración es válida
            
        Raises:
            ValueError: Si la fuente no existe o la configuración no es válida
        """
        source = self.get_source_by_id(source_id)
        
        # Verificar que todos los campos requeridos estén presentes
        for field, field_type in source.config_schema.items():
            if field not in config:
                raise ValueError(f"Campo requerido faltante: {field}")
            
            # Verificación básica de tipos
            if field_type == "string" and not isinstance(config[field], str):
                raise ValueError(f"El campo {field} debe ser una cadena")
            elif field_type == "boolean" and not isinstance(config[field], bool):
                raise ValueError(f"El campo {field} debe ser un booleano")
            elif field_type == "array" and not isinstance(config[field], list):
                raise ValueError(f"El campo {field} debe ser una lista")
            elif field_type == "object" and not isinstance(config[field], dict):
                raise ValueError(f"El campo {field} debe ser un objeto")
        
        return True 