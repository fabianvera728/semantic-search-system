import csv
import json
import os
from datetime import datetime
from typing import Dict, Any, List

from src.domain.entities.harvested_data import HarvestedData, DataColumn
from src.domain.ports.harvester_port import HarvesterPort


class FileHarvesterAdapter(HarvesterPort):
    """
    Adaptador que implementa la cosecha de datos desde archivos.
    
    Este adaptador soporta la cosecha de datos desde archivos CSV y JSON.
    """
    
    async def harvest(self, config: Dict[str, Any]) -> HarvestedData:
        """
        Cosecha datos de un archivo según la configuración proporcionada.
        
        Args:
            config: Configuración específica para la cosecha
                - file_path: Ruta del archivo
                - file_type: Tipo de archivo (csv, json)
                - delimiter: Delimitador para CSV (opcional, por defecto ',')
                - has_header: Si el CSV tiene encabezado (opcional, por defecto True)
                - root_path: Ruta raíz para JSON (opcional)
            
        Returns:
            Los datos cosechados
            
        Raises:
            ValueError: Si la configuración es inválida o la cosecha falla
        """
        # Validar configuración
        if "file_path" not in config:
            raise ValueError("La ruta del archivo es requerida para la cosecha")
        
        file_path = config["file_path"]
        
        # Verificar que el archivo existe
        if not os.path.exists(file_path):
            raise ValueError(f"Archivo no encontrado: {file_path}")
        
        # Determinar el tipo de archivo
        file_type = config.get("file_type", "").lower()
        if not file_type:
            file_extension = os.path.splitext(file_path)[1].lower()
            file_type = file_extension.replace(".", "")
        
        # Procesar archivo según su tipo
        if file_type == "csv":
            return await self._process_csv(file_path, config)
        elif file_type == "json":
            return await self._process_json(file_path, config)
        else:
            raise ValueError(f"Tipo de archivo no soportado: {file_type}")
    
    async def _process_csv(self, file_path: str, config: Dict[str, Any]) -> HarvestedData:
        """
        Procesa un archivo CSV.
        
        Args:
            file_path: Ruta del archivo CSV
            config: Configuración para el procesamiento
            
        Returns:
            Los datos cosechados
        """
        delimiter = config.get("delimiter", ",")
        has_header = config.get("has_header", True)
        
        rows = []
        columns = []
        
        with open(file_path, "r", encoding="utf-8") as f:
            csv_reader = csv.reader(f, delimiter=delimiter)
            
            # Leer encabezado
            header = []
            if has_header:
                header = next(csv_reader)
                
                # Crear columnas
                for column_name in header:
                    columns.append(DataColumn(
                        name=column_name,
                        type="string"  # Tipo por defecto
                    ))
            
            # Leer datos
            for csv_row in csv_reader:
                # Crear datos de fila
                if has_header:
                    row_data = {header[i]: value for i, value in enumerate(csv_row) if i < len(header)}
                else:
                    row_data = {f"column_{i}": value for i, value in enumerate(csv_row)}
                
                # Añadir metadatos de importación
                row_data["import_timestamp"] = datetime.utcnow().isoformat()
                row_data["source_file"] = os.path.basename(file_path)
                
                # Añadir fila
                rows.append(row_data)
        
        # Si no hay encabezado, crear columnas a partir de la primera fila
        if not has_header and rows:
            for key in rows[0].keys():
                columns.append(DataColumn(
                    name=key,
                    type="string"  # Tipo por defecto
                ))
        
        # Crear metadatos
        metadata = {
            "file_name": os.path.basename(file_path),
            "file_size": os.path.getsize(file_path),
            "delimiter": delimiter,
            "has_header": has_header,
            "import_timestamp": datetime.utcnow().isoformat()
        }
        
        # Crear y retornar datos cosechados
        return HarvestedData(
            source_type="file",
            source_identifier=file_path,
            rows=rows,
            columns=columns,
            metadata=metadata
        )
    
    async def _process_json(self, file_path: str, config: Dict[str, Any]) -> HarvestedData:
        """
        Procesa un archivo JSON.
        
        Args:
            file_path: Ruta del archivo JSON
            config: Configuración para el procesamiento
            
        Returns:
            Los datos cosechados
        """
        root_path = config.get("root_path", "")
        
        with open(file_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)
            
            # Obtener datos desde la ruta raíz
            if root_path:
                parts = root_path.split(".")
                data = json_data
                for part in parts:
                    if part in data:
                        data = data[part]
                    else:
                        raise ValueError(f"Ruta raíz '{root_path}' no encontrada en los datos JSON")
            else:
                data = json_data
            
            # Asegurar que los datos sean una lista
            if not isinstance(data, list):
                data = [data]
            
            # Procesar datos
            rows = []
            for item in data:
                if not isinstance(item, dict):
                    continue
                
                # Añadir metadatos de importación
                item_copy = item.copy()
                item_copy["import_timestamp"] = datetime.utcnow().isoformat()
                item_copy["source_file"] = os.path.basename(file_path)
                
                # Añadir fila
                rows.append(item_copy)
            
            # Crear columnas a partir de la primera fila
            columns = []
            if rows:
                for key in rows[0].keys():
                    columns.append(DataColumn(
                        name=key,
                        type="string"  # Tipo por defecto
                    ))
            
            # Crear metadatos
            metadata = {
                "file_name": os.path.basename(file_path),
                "file_size": os.path.getsize(file_path),
                "root_path": root_path,
                "import_timestamp": datetime.utcnow().isoformat()
            }
            
            # Crear y retornar datos cosechados
            return HarvestedData(
                source_type="file",
                source_identifier=file_path,
                rows=rows,
                columns=columns,
                metadata=metadata
            ) 