import aiohttp
import asyncio
from typing import Dict, Any, List, Optional
import json


class APIHarvester:
    """Cosechador de datos desde APIs REST."""
    
    def __init__(self):
        self.session = None
    
    async def harvest(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cosecha datos desde una API REST.
        
        Args:
            config: Configuración que debe incluir:
                - url: URL de la API
                - method: Método HTTP (GET, POST, etc.)
                - headers: Headers HTTP opcionales
                - params: Parámetros de query opcionales
                - data: Datos para POST/PUT opcionales
                - auth: Configuración de autenticación opcional
                
        Returns:
            Diccionario con los datos cosechados
        """
        url = config.get("url")
        method = config.get("method", "GET").upper()
        headers = config.get("headers", {})
        params = config.get("params", {})
        data = config.get("data")
        auth_config = config.get("auth", {})
        
        if not url:
            raise ValueError("url is required")
        
        # Configurar autenticación si se proporciona
        if auth_config:
            headers.update(self._setup_auth(auth_config))
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=data if data else None
                ) as response:
                    
                    if response.status >= 400:
                        raise Exception(f"API request failed with status {response.status}: {await response.text()}")
                    
                    content_type = response.headers.get("content-type", "").lower()
                    
                    if "application/json" in content_type:
                        response_data = await response.json()
                    else:
                        response_text = await response.text()
                        try:
                            response_data = json.loads(response_text)
                        except json.JSONDecodeError:
                            response_data = {"raw_data": response_text}
                    
                    return self._process_api_response(response_data, url)
                    
        except Exception as e:
            raise Exception(f"Error harvesting from API {url}: {str(e)}")
    
    def _setup_auth(self, auth_config: Dict[str, Any]) -> Dict[str, str]:
        """Configura la autenticación para la API."""
        auth_type = auth_config.get("type", "").lower()
        headers = {}
        
        if auth_type == "bearer":
            token = auth_config.get("token")
            if token:
                headers["Authorization"] = f"Bearer {token}"
        elif auth_type == "api_key":
            api_key = auth_config.get("api_key")
            key_header = auth_config.get("header", "X-API-Key")
            if api_key:
                headers[key_header] = api_key
        elif auth_type == "basic":
            # Para Basic Auth, se manejaría con aiohttp.BasicAuth
            # Por simplicidad, aquí solo documentamos la estructura
            pass
        
        return headers
    
    def _process_api_response(self, response_data: Any, url: str) -> Dict[str, Any]:
        """Procesa la respuesta de la API para extraer datos estructurados."""
        
        # Intentar extraer datos en formato tabular
        data = []
        columns = []
        row_count = 0
        
        if isinstance(response_data, list):
            # Lista de objetos
            data = response_data
            if data and isinstance(data[0], dict):
                columns = list(data[0].keys())
            row_count = len(data)
            
        elif isinstance(response_data, dict):
            # Buscar arrays comunes en respuestas de API
            possible_data_keys = ["data", "results", "items", "records", "rows"]
            
            for key in possible_data_keys:
                if key in response_data and isinstance(response_data[key], list):
                    data = response_data[key]
                    if data and isinstance(data[0], dict):
                        columns = list(data[0].keys())
                    row_count = len(data)
                    break
            
            # Si no se encontró un array, usar el objeto completo
            if not data:
                data = [response_data]
                columns = list(response_data.keys())
                row_count = 1
        
        else:
            # Datos primitivos
            data = [{"value": response_data}]
            columns = ["value"]
            row_count = 1
        
        return {
            "data": data,
            "columns": columns,
            "row_count": row_count,
            "api_info": {
                "url": url,
                "response_type": type(response_data).__name__
            }
        } 