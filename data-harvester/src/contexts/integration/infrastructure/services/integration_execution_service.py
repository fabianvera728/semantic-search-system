import httpx
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from ...domain.entities import DataIntegration, IntegrationJob, JobStatus
from src.contexts.harvest.infrastructure.harvesters.file_harvester import FileHarvester
from src.contexts.harvest.infrastructure.harvesters.api_harvester import APIHarvester
from src.contexts.harvest.infrastructure.harvesters.web_harvester import WebHarvester
from .jwt_service import JWTService


class IntegrationExecutionService:
    """Servicio para ejecutar integraciones completas: cosecha → procesamiento → almacenamiento."""
    
    def __init__(self):
        self.data_processor_url = "http://data-processor:8004"
        self.data_storage_url = "http://data-storage:8003"
        self.jwt_service = JWTService()
        self.harvesters = {
            "file": FileHarvester(),
            "api": APIHarvester(),
            "web": WebHarvester()
        }
    
    async def execute_integration(self, integration: DataIntegration, job: IntegrationJob) -> Dict[str, Any]:
        """
        Ejecuta una integración completa.
        
        Args:
            integration: La integración a ejecutar
            job: El job de integración
            
        Returns:
            Resultado de la ejecución
        """
        try:
            # Paso 0: Obtener información del dataset para mapeo
            job.add_log("Obteniendo información del dataset...")
            dataset_info = await self._get_dataset_info(integration.dataset_id)
            if not dataset_info:
                raise Exception(f"No se pudo obtener información del dataset {integration.dataset_id}")
            
            job.add_log(f"Dataset encontrado: {dataset_info.get('name')} con {len(dataset_info.get('columns', []))} columnas")
            
            # Paso 1: Cosecha de datos
            job.add_log("Iniciando cosecha de datos...")
            harvested_data = await self._harvest_data(integration)
            
            if not harvested_data or not harvested_data.get("data"):
                raise Exception("No se obtuvieron datos de la cosecha")
            
            job.add_log(f"Cosecha completada: {len(harvested_data['data'])} registros obtenidos")
            
            # Paso 2: Procesamiento de datos (si hay configuración)
            processed_data = harvested_data["data"]
            if integration.processing_config and integration.processing_config.get("operations"):
                job.add_log("Iniciando procesamiento de datos...")
                processed_data = await self._process_data(harvested_data["data"], integration.processing_config)
                job.add_log(f"Procesamiento completado: {len(processed_data)} registros procesados")
            else:
                job.add_log("Sin configuración de procesamiento, usando datos originales")
            
            # Paso 3: Mapear datos a las columnas del dataset
            job.add_log("Iniciando mapeo de datos...")
            mapped_data = await self._map_data_to_dataset_columns(
                processed_data, 
                dataset_info, 
                integration.harvest_config.get("column_mapping", {}),
                harvested_data.get("columns", [])
            )
            job.add_log(f"Mapeo completado: {len(mapped_data)} registros mapeados")
            
            # Paso 4: Almacenamiento en dataset
            job.add_log("Iniciando almacenamiento en dataset...")
            storage_result = await self._store_data(integration.dataset_id, mapped_data, list(dataset_info.get('columns', [])))
            job.add_log(f"Almacenamiento completado: {storage_result.get('rows_added', 0)} filas agregadas")
            
            # Resultado final
            result = {
                "harvest_info": {
                    "source_type": integration.harvest_config["source_type"],
                    "records_harvested": len(harvested_data["data"]),
                    "columns": harvested_data.get("columns", []),
                    "file_info": harvested_data.get("file_info")
                },
                "processing_info": {
                    "operations_applied": len(integration.processing_config.get("operations", [])) if integration.processing_config else 0,
                    "records_processed": len(processed_data)
                },
                "mapping_info": {
                    "dataset_columns": [col.get('name') for col in dataset_info.get('columns', [])],
                    "mapped_records": len(mapped_data)
                },
                "storage_info": storage_result,
                "execution_summary": {
                    "total_records": len(mapped_data),
                    "dataset_id": integration.dataset_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
            return result
            
        except Exception as e:
            job.add_log(f"Error en la ejecución: {str(e)}")
            raise
    
    async def _get_dataset_info(self, dataset_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene información del dataset incluyendo sus columnas."""
        try:
            auth_headers = self.jwt_service.get_auth_headers("data-harvester")
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.data_storage_url}/datasets/{dataset_id}",
                    headers=auth_headers
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    print(f"❌ Error obteniendo dataset info: {response.status_code}")
                    return None
                    
        except Exception as e:
            print(f"❌ Excepción obteniendo dataset info: {str(e)}")
            return None
    
    async def _map_data_to_dataset_columns(
        self, 
        data: List[Dict[str, Any]], 
        dataset_info: Dict[str, Any],
        column_mapping: Dict[str, str],
        harvested_columns: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Mapea los datos cosechados a las columnas del dataset.
        
        Args:
            data: Datos procesados
            dataset_info: Información del dataset incluyendo columnas
            column_mapping: Mapeo explícito de columnas fuente -> dataset
            harvested_columns: Columnas encontradas en los datos cosechados
            
        Returns:
            Datos mapeados según las columnas del dataset
        """
        dataset_columns = dataset_info.get('columns', [])
        
        print(f"🔍 MAPPING - Dataset columns: {[col.get('name') for col in dataset_columns]}")
        print(f"🔍 MAPPING - Harvested columns: {harvested_columns}")
        print(f"🔍 MAPPING - Explicit mapping: {column_mapping}")
        
        if not dataset_columns:
            print("⚠️ MAPPING - No se encontraron columnas en el dataset, usando datos originales")
            return data
        
        # Crear mapeo de columnas
        column_map = {}
        
        # 1. Usar mapeo explícito si está disponible
        for source_col, target_col in column_mapping.items():
            column_map[source_col] = target_col
            print(f"🔍 MAPPING - Mapeo explícito: {source_col} -> {target_col}")
        
        # 2. Mapeo automático por nombre exacto
        dataset_column_names = {col.get('name') for col in dataset_columns}
        for harvested_col in harvested_columns:
            if harvested_col not in column_map and harvested_col in dataset_column_names:
                column_map[harvested_col] = harvested_col
                print(f"🔍 MAPPING - Mapeo automático: {harvested_col} -> {harvested_col}")
        
        # 3. Mapear datos
        mapped_data = []
        for row_index, row in enumerate(data):
            mapped_row = {}
            
            # Mapear columnas conocidas
            for source_col, target_col in column_map.items():
                if source_col in row:
                    mapped_row[target_col] = row[source_col]
            
            # Agregar valores por defecto para columnas faltantes
            for col in dataset_columns:
                col_name = col.get('name')
                if col_name not in mapped_row:
                    col_type = col.get('type', 'string')
                    # Valores por defecto según el tipo
                    if col_type == 'string':
                        mapped_row[col_name] = ""
                    elif col_type == 'number':
                        mapped_row[col_name] = 0
                    elif col_type == 'boolean':
                        mapped_row[col_name] = False
                    elif col_type == 'date':
                        mapped_row[col_name] = None
                    else:
                        mapped_row[col_name] = None
            
            if row_index < 3:  # Log primeras 3 filas para debug
                print(f"🔍 MAPPING - Fila {row_index}: {row} -> {mapped_row}")
            
            mapped_data.append(mapped_row)
        
        print(f"🔍 MAPPING - Mapeo completado: {len(mapped_data)} filas mapeadas")
        return mapped_data

    async def _harvest_data(self, integration: DataIntegration) -> Dict[str, Any]:
        """Cosecha datos usando el harvester apropiado."""
        source_type = integration.harvest_config["source_type"]
        config = integration.harvest_config["config"]
        
        if source_type not in self.harvesters:
            raise ValueError(f"Tipo de fuente no soportado: {source_type}")
        
        harvester = self.harvesters[source_type]
        return await harvester.harvest(config)
    
    async def _process_data(self, data: List[Dict[str, Any]], processing_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Procesa los datos usando el data-processor."""
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:  # 5 minutos timeout
                response = await client.post(
                    f"{self.data_processor_url}/process",
                    json={
                        "dataset": data,
                        "operations": processing_config.get("operations", [])
                    }
                )
                response.raise_for_status()
                
                # El data-processor devuelve un job_id, necesitamos esperar el resultado
                result = response.json()
                job_id = result.get("job_id")
                
                if not job_id:
                    raise Exception("No se recibió job_id del data-processor")
                
                # Esperar a que termine el procesamiento
                return await self._wait_for_processing_completion(job_id)
                
        except httpx.RequestError as e:
            raise Exception(f"Error comunicándose con data-processor: {str(e)}")
        except httpx.HTTPStatusError as e:
            raise Exception(f"Error HTTP del data-processor: {e.response.status_code} - {e.response.text}")
    
    async def _wait_for_processing_completion(self, job_id: str, max_wait_seconds: int = 300) -> List[Dict[str, Any]]:
        """Espera a que termine el procesamiento y devuelve los datos procesados."""
        start_time = datetime.utcnow()
        
        while (datetime.utcnow() - start_time).total_seconds() < max_wait_seconds:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{self.data_processor_url}/jobs/{job_id}")
                    response.raise_for_status()
                    
                    job_status = response.json()
                    status = job_status.get("status")
                    
                    if status == "completed":
                        data = job_status.get("data")
                        if data and "data" in data:
                            return data["data"]
                        else:
                            raise Exception("No se encontraron datos procesados en el resultado")
                    elif status == "failed":
                        error_msg = job_status.get("message", "Error desconocido en el procesamiento")
                        raise Exception(f"Procesamiento falló: {error_msg}")
                    
                    # Si está en progreso, esperar un poco más
                    await asyncio.sleep(2)
                    
            except httpx.RequestError:
                # Si hay error de conexión, esperar y reintentar
                await asyncio.sleep(5)
        
        raise Exception(f"Timeout esperando completar el procesamiento del job {job_id}")
    
    async def _store_data(self, dataset_id: str, data: List[Dict[str, Any]], columns: List[str]) -> Dict[str, Any]:
        """Almacena los datos procesados en el dataset."""
        try:
            # Obtener headers de autenticación JWT
            auth_headers = self.jwt_service.get_auth_headers("data-harvester")
            
            # Primero verificar que el dataset existe
            async with httpx.AsyncClient() as client:
                # Verificar dataset
                dataset_response = await client.get(
                    f"{self.data_storage_url}/datasets/{dataset_id}",
                    headers=auth_headers
                )
                
                if dataset_response.status_code == 404:
                    raise Exception(f"Dataset {dataset_id} no encontrado")
                elif dataset_response.status_code != 200:
                    raise Exception(f"Error verificando dataset: {dataset_response.status_code}")
                
                # Agregar filas al dataset
                rows_added = 0
                failed_rows = 0
                
                for row_index, row_data in enumerate(data):
                    try:
                        payload = {"data": row_data}
                        print(f"🔍 HARVESTER - Enviando fila {row_index + 1}/{len(data)}")
                        print(f"🔍 HARVESTER - Dataset ID: {dataset_id}")
                        print(f"🔍 HARVESTER - Payload: {payload}")
                        print(f"🔍 HARVESTER - Headers: {auth_headers}")
                        
                        row_response = await client.post(
                            f"{self.data_storage_url}/datasets/{dataset_id}/rows",
                            json=payload,
                            headers=auth_headers
                        )
                        
                        print(f"🔍 HARVESTER - Respuesta fila {row_index + 1}: {row_response.status_code}")
                        if row_response.status_code not in [200, 201]:
                            print(f"❌ HARVESTER - Error fila {row_index + 1}: {row_response.text}")
                        
                        if row_response.status_code in [200, 201]:
                            rows_added += 1
                            print(f"✅ HARVESTER - Fila {row_index + 1} agregada exitosamente")
                        else:
                            failed_rows += 1
                            print(f"❌ HARVESTER - Error en fila {row_index + 1}: {row_response.status_code}")
                            
                    except Exception as e:
                        failed_rows += 1
                        print(f"❌ HARVESTER - Excepción en fila {row_index + 1}: {str(e)}")
                        continue
                
                return {
                    "dataset_id": dataset_id,
                    "rows_added": rows_added,
                    "rows_failed": failed_rows,
                    "total_rows": len(data),
                    "success_rate": (rows_added / len(data)) * 100 if data else 0
                }
                
        except httpx.RequestError as e:
            raise Exception(f"Error comunicándose con data-storage: {str(e)}")
        except httpx.HTTPStatusError as e:
            raise Exception(f"Error HTTP del data-storage: {e.response.status_code} - {e.response.text}") 