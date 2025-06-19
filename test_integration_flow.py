#!/usr/bin/env python3
"""
Script de prueba para verificar el flujo completo de integración.
Prueba: Cosecha → Procesamiento → Almacenamiento
"""

import asyncio
import httpx
import json
import time
from typing import Dict, Any

# URLs de los servicios
DATA_HARVESTER_URL = "http://localhost:8002"
DATA_PROCESSOR_URL = "http://localhost:8004"
DATA_STORAGE_URL = "http://localhost:8003"

async def test_data_processor_directly():
    """Prueba el data-processor directamente para verificar que funciona."""
    print("🧪 Probando data-processor directamente...")
    
    # Datos de prueba
    test_data = [
        {"name": "Juan", "age": 25, "city": "Madrid"},
        {"name": "María", "age": 30, "city": "Barcelona"},
        {"name": "Pedro", "age": 35, "city": "Valencia"}
    ]
    
    # Operaciones de prueba (si están disponibles)
    test_operations = []
    
    try:
        async with httpx.AsyncClient() as client:
            # 1. Verificar que el servicio esté funcionando
            response = await client.get(f"{DATA_PROCESSOR_URL}/")
            print(f"✅ Data-processor está funcionando: {response.json()}")
            
            # 2. Obtener operaciones disponibles
            response = await client.get(f"{DATA_PROCESSOR_URL}/operations")
            operations = response.json().get("operations", [])
            print(f"📋 Operaciones disponibles: {len(operations)}")
            
            # 3. Iniciar procesamiento
            response = await client.post(f"{DATA_PROCESSOR_URL}/process", json={
                "dataset": test_data,
                "operations": test_operations
            })
            
            if response.status_code != 200:
                print(f"❌ Error iniciando procesamiento: {response.status_code} - {response.text}")
                return False
            
            result = response.json()
            job_id = result.get("job_id")
            print(f"🚀 Procesamiento iniciado con job_id: {job_id}")
            
            # 4. Esperar resultado
            max_attempts = 30
            for attempt in range(max_attempts):
                response = await client.get(f"{DATA_PROCESSOR_URL}/jobs/{job_id}")
                
                if response.status_code != 200:
                    print(f"❌ Error consultando job: {response.status_code}")
                    return False
                
                job_status = response.json()
                status = job_status.get("status")
                print(f"📊 Intento {attempt + 1}: Status = {status}")
                
                if status == "completed":
                    data = job_status.get("data")
                    if data and "data" in data:
                        processed_data = data["data"]
                        print(f"✅ Procesamiento completado: {len(processed_data)} registros")
                        print(f"📄 Datos procesados: {processed_data[:2]}...")  # Mostrar primeros 2
                        return True
                    else:
                        print("❌ No se encontraron datos en el resultado")
                        return False
                elif status == "failed":
                    error_msg = job_status.get("message", "Error desconocido")
                    print(f"❌ Procesamiento falló: {error_msg}")
                    return False
                
                await asyncio.sleep(2)
            
            print("❌ Timeout esperando resultado del procesamiento")
            return False
            
    except Exception as e:
        print(f"❌ Error probando data-processor: {str(e)}")
        return False

async def test_integration_flow():
    """Prueba el flujo completo de integración."""
    print("\n🔄 Probando flujo completo de integración...")
    
    # Crear datos de prueba en un archivo temporal
    import tempfile
    import csv
    import os
    
    # Crear archivo CSV temporal
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['name', 'age', 'city', 'salary'])
        writer.writerow(['Juan', '25', 'Madrid', '30000'])
        writer.writerow(['María', '30', 'Barcelona', '35000'])
        writer.writerow(['Pedro', '35', 'Valencia', '40000'])
        writer.writerow(['Ana', '28', 'Sevilla', '32000'])
        temp_file_path = f.name
    
    print(f"📁 Archivo temporal creado: {temp_file_path}")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            # 1. Verificar que data-harvester esté funcionando
            response = await client.get(f"{DATA_HARVESTER_URL}/")
            print(f"✅ Data-harvester está funcionando")
            
            # 2. Crear una integración de prueba
            integration_data = {
                "name": "Test Integration",
                "description": "Integración de prueba para el flujo completo",
                "dataset_id": "test-dataset-id-12345",  # ID ficticio para prueba - fallará en almacenamiento pero probará cosecha y procesamiento
                "harvest_config": {
                    "source_type": "file",
                    "config": {
                        "file_path": temp_file_path,
                        "file_type": "csv",
                        "options": {
                            "separator": ",",
                            "encoding": "utf-8"
                        }
                    }
                },
                "processing_config": {
                    "operations": []  # Sin operaciones por ahora
                },
                "is_active": True
            }
            
            response = await client.post(f"{DATA_HARVESTER_URL}/api/integrations", json=integration_data)
            
            if response.status_code != 200:
                print(f"❌ Error creando integración: {response.status_code} - {response.text}")
                return False
            
            integration = response.json()
            integration_id = integration["id"]
            print(f"✅ Integración creada: {integration_id}")
            
            # 3. Ejecutar la integración
            response = await client.post(f"{DATA_HARVESTER_URL}/api/integrations/{integration_id}/run")
            
            if response.status_code != 200:
                print(f"❌ Error ejecutando integración: {response.status_code} - {response.text}")
                return False
            
            job = response.json()
            job_id = job["id"]
            print(f"🚀 Integración ejecutándose con job_id: {job_id}")
            
            # 4. Monitorear progreso
            max_attempts = 60  # 2 minutos máximo
            for attempt in range(max_attempts):
                response = await client.get(f"{DATA_HARVESTER_URL}/api/jobs/{job_id}")
                
                if response.status_code != 200:
                    print(f"❌ Error consultando job: {response.status_code}")
                    return False
                
                job_status = response.json()
                status = job_status.get("status")
                logs = job_status.get("logs", [])
                
                print(f"📊 Intento {attempt + 1}: Status = {status}")
                
                # Mostrar logs más recientes
                if logs:
                    for log in logs[-2:]:  # Últimos 2 logs
                        print(f"   📝 {log}")
                
                if status == "completed":
                    result = job_status.get("result", {})
                    print(f"✅ Integración completada exitosamente!")
                    print(f"📊 Estadísticas:")
                    
                    harvest_info = result.get("harvest_info", {})
                    processing_info = result.get("processing_info", {})
                    storage_info = result.get("storage_info", {})
                    
                    print(f"   📥 Cosecha: {harvest_info.get('records_harvested', 0)} registros")
                    print(f"   ⚙️ Procesamiento: {processing_info.get('records_processed', 0)} registros")
                    print(f"   💾 Almacenamiento: {storage_info.get('rows_added', 0)} filas agregadas")
                    print(f"   📈 Tasa de éxito: {storage_info.get('success_rate', 0):.1f}%")
                    
                    return True
                    
                elif status == "failed":
                    error_msg = job_status.get("error_message", "Error desconocido")
                    print(f"❌ Integración falló: {error_msg}")
                    
                    # Mostrar todos los logs para debugging
                    if logs:
                        print("📝 Logs completos:")
                        for log in logs:
                            print(f"   {log}")
                    
                    return False
                
                await asyncio.sleep(2)
            
            print("❌ Timeout esperando resultado de la integración")
            return False
            
    except Exception as e:
        print(f"❌ Error probando integración: {str(e)}")
        return False
    finally:
        # Limpiar archivo temporal
        try:
            os.unlink(temp_file_path)
            print(f"🗑️ Archivo temporal eliminado")
        except:
            pass

async def main():
    """Función principal de pruebas."""
    print("🧪 Iniciando pruebas del flujo de integración")
    print("=" * 50)
    
    # Prueba 1: Data-processor directamente
    processor_ok = await test_data_processor_directly()
    
    if not processor_ok:
        print("\n❌ El data-processor no está funcionando correctamente")
        print("   Verifica que el servicio esté ejecutándose en el puerto 8004")
        return
    
    # Prueba 2: Flujo completo de integración
    integration_ok = await test_integration_flow()
    
    print("\n" + "=" * 50)
    if integration_ok:
        print("🎉 ¡Todas las pruebas pasaron exitosamente!")
        print("✅ El flujo Cosecha → Procesamiento → Almacenamiento funciona correctamente")
    else:
        print("❌ Las pruebas fallaron")
        print("   Revisa los logs de los servicios para más detalles")

if __name__ == "__main__":
    asyncio.run(main()) 