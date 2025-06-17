import pandas as pd
import json
from typing import Dict, Any, List
from pathlib import Path


class FileHarvester:
    """Cosechador de datos desde archivos."""
    
    async def harvest(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cosecha datos desde un archivo.
        
        Args:
            config: Configuración que debe incluir:
                - file_path: Ruta del archivo
                - file_type: Tipo de archivo (csv, json, excel)
                - options: Opciones específicas del tipo de archivo
                
        Returns:
            Diccionario con los datos cosechados
        """
        file_path = config.get("file_path")
        file_type = config.get("file_type", "csv")
        options = config.get("options", {})
        
        if not file_path:
            raise ValueError("file_path is required")
        
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            if file_type.lower() == "csv":
                return await self._harvest_csv(path, options)
            elif file_type.lower() == "json":
                return await self._harvest_json(path, options)
            elif file_type.lower() in ["xlsx", "xls", "excel"]:
                return await self._harvest_excel(path, options)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
                
        except Exception as e:
            raise Exception(f"Error harvesting file {file_path}: {str(e)}")
    
    async def _harvest_csv(self, file_path: Path, options: Dict[str, Any]) -> Dict[str, Any]:
        """Cosecha datos desde archivo CSV."""
        separator = options.get("separator", ",")
        encoding = options.get("encoding", "utf-8")
        
        df = pd.read_csv(file_path, sep=separator, encoding=encoding)
        
        return {
            "data": df.to_dict("records"),
            "columns": list(df.columns),
            "row_count": len(df),
            "file_info": {
                "name": file_path.name,
                "size": file_path.stat().st_size,
                "type": "csv"
            }
        }
    
    async def _harvest_json(self, file_path: Path, options: Dict[str, Any]) -> Dict[str, Any]:
        """Cosecha datos desde archivo JSON."""
        encoding = options.get("encoding", "utf-8")
        
        with open(file_path, "r", encoding=encoding) as f:
            data = json.load(f)
        
        # Si es una lista de objetos, extraer columnas
        columns = []
        row_count = 0
        
        if isinstance(data, list) and data:
            if isinstance(data[0], dict):
                columns = list(data[0].keys())
                row_count = len(data)
        elif isinstance(data, dict):
            columns = list(data.keys())
            row_count = 1
            data = [data]  # Convertir a lista para consistencia
        
        return {
            "data": data,
            "columns": columns,
            "row_count": row_count,
            "file_info": {
                "name": file_path.name,
                "size": file_path.stat().st_size,
                "type": "json"
            }
        }
    
    async def _harvest_excel(self, file_path: Path, options: Dict[str, Any]) -> Dict[str, Any]:
        """Cosecha datos desde archivo Excel."""
        sheet_name = options.get("sheet_name", 0)  # Primera hoja por defecto
        
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        
        return {
            "data": df.to_dict("records"),
            "columns": list(df.columns),
            "row_count": len(df),
            "file_info": {
                "name": file_path.name,
                "size": file_path.stat().st_size,
                "type": "excel"
            }
        } 