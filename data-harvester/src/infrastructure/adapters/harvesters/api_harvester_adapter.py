import aiohttp
from datetime import datetime
from typing import Dict, Any, List

from src.domain.entities.harvested_data import HarvestedData, DataColumn
from src.domain.ports.harvester_port import HarvesterPort


class APIHarvesterAdapter(HarvesterPort):
    
    async def harvest(self, config: Dict[str, Any]) -> HarvestedData:
        if "url" not in config:
            raise ValueError("La URL es requerida para la cosecha de API")
        
        url = config["url"]
        method = config.get("method", "GET").upper()
        headers = config.get("headers", {})
        params = config.get("params", {})
        data = config.get("data", {})
        auth = config.get("auth", None)
        root_path = config.get("root_path", "")
        
        # Realizar solicitud a la API
        async with aiohttp.ClientSession() as session:
            # Preparar autenticación
            auth_tuple = None
            if auth and isinstance(auth, dict) and "username" in auth and "password" in auth:
                auth_tuple = aiohttp.BasicAuth(auth["username"], auth["password"])
            
            # Realizar solicitud
            try:
                if method == "GET":
                    async with session.get(url, headers=headers, params=params, auth=auth_tuple) as response:
                        if response.status == 200:
                            response_data = await response.json()
                        else:
                            raise ValueError(f"La solicitud a la API falló con estado {response.status}")
                elif method == "POST":
                    async with session.post(url, headers=headers, params=params, json=data, auth=auth_tuple) as response:
                        if response.status == 200:
                            response_data = await response.json()
                        else:
                            raise ValueError(f"La solicitud a la API falló con estado {response.status}")
                else:
                    raise ValueError(f"Método HTTP no soportado: {method}")
            except Exception as e:
                raise ValueError(f"Error en la solicitud a la API: {str(e)}")
            
            # Obtener datos desde la ruta raíz
            if root_path:
                parts = root_path.split(".")
                result_data = response_data
                for part in parts:
                    if part in result_data:
                        result_data = result_data[part]
                    else:
                        raise ValueError(f"Ruta raíz '{root_path}' no encontrada en la respuesta de la API")
            else:
                result_data = response_data
            
            # Asegurar que los datos sean una lista
            if not isinstance(result_data, list):
                result_data = [result_data]
            
            # Procesar datos
            rows = []
            for item in result_data:
                if not isinstance(item, dict):
                    continue
                
                # Añadir metadatos de importación
                item_copy = item.copy()
                item_copy["import_timestamp"] = datetime.utcnow().isoformat()
                item_copy["source_api"] = url
                
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
                "api_url": url,
                "method": method,
                "root_path": root_path,
                "import_timestamp": datetime.utcnow().isoformat()
            }
            
            # Crear y retornar datos cosechados
            return HarvestedData(
                source_type="api",
                source_identifier=url,
                rows=rows,
                columns=columns,
                metadata=metadata
            ) 