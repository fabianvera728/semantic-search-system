#!/usr/bin/env python3
"""
Script de prueba para verificar la autenticación JWT entre servicios.
"""

import asyncio
import httpx
import sys
import os

# Agregar el path del data-harvester para importar el JWT service
sys.path.append(os.path.join(os.path.dirname(__file__), 'semantic-search-system', 'data-harvester'))

from src.contexts.integration.infrastructure.services.jwt_service import JWTService

# URLs de los servicios
DATA_STORAGE_URL = "http://localhost:8003"

async def test_jwt_authentication():
    """Prueba la autenticación JWT con data-storage."""
    print("🔐 Probando autenticación JWT entre servicios...")
    
    try:
        # Crear servicio JWT
        jwt_service = JWTService()
        
        # Generar token
        token = jwt_service.generate_service_token("data-harvester")
        print(f"✅ Token JWT generado: {token[:50]}...")
        
        # Obtener headers de autenticación
        auth_headers = jwt_service.get_auth_headers("data-harvester")
        print(f"✅ Headers de autenticación generados")
        
        # Probar acceso a data-storage
        async with httpx.AsyncClient() as client:
            # 1. Probar endpoint público (debería funcionar sin token)
            response = await client.get(f"{DATA_STORAGE_URL}/")
            print(f"✅ Endpoint público (/): {response.status_code}")
            
            # 2. Probar endpoint que requiere autenticación
            response = await client.get(f"{DATA_STORAGE_URL}/datasets", headers=auth_headers)
            
            if response.status_code == 200:
                print(f"✅ Autenticación JWT exitosa: {response.status_code}")
                datasets = response.json()
                print(f"📊 Datasets encontrados: {len(datasets)}")
                return True
            elif response.status_code == 401:
                print(f"❌ Error de autenticación: {response.status_code}")
                print(f"   Respuesta: {response.text}")
                return False
            elif response.status_code == 403:
                print(f"❌ Error de autorización: {response.status_code}")
                print(f"   Respuesta: {response.text}")
                return False
            else:
                print(f"⚠️ Respuesta inesperada: {response.status_code}")
                print(f"   Respuesta: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Error probando autenticación JWT: {str(e)}")
        return False

async def test_dataset_creation():
    """Prueba crear un dataset real para las pruebas de integración."""
    print("\n📁 Probando creación de dataset para pruebas...")
    
    try:
        jwt_service = JWTService()
        auth_headers = jwt_service.get_auth_headers("data-harvester")
        
        # Datos del dataset de prueba
        dataset_data = {
            "name": "Test Dataset for Integration",
            "description": "Dataset de prueba para integraciones",
            "tags": ["test", "integration"],
            "is_public": False,
            "columns": [
                {"name": "name", "type": "string", "description": "Nombre"},
                {"name": "age", "type": "integer", "description": "Edad"},
                {"name": "city", "type": "string", "description": "Ciudad"},
                {"name": "salary", "type": "integer", "description": "Salario"}
            ],
            "rows": []  # Sin datos iniciales
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{DATA_STORAGE_URL}/datasets",
                json=dataset_data,
                headers=auth_headers
            )
            
            if response.status_code in [200, 201]:
                dataset = response.json()
                dataset_id = dataset.get("id")
                print(f"✅ Dataset creado exitosamente: {dataset_id}")
                print(f"   Nombre: {dataset.get('name')}")
                print(f"   Columnas: {len(dataset.get('columns', []))}")
                return dataset_id
            else:
                print(f"❌ Error creando dataset: {response.status_code}")
                print(f"   Respuesta: {response.text}")
                return None
                
    except Exception as e:
        print(f"❌ Error creando dataset: {str(e)}")
        return None

async def test_dataset_access(dataset_id: str):
    """Prueba acceso a un dataset específico."""
    print(f"\n🔍 Probando acceso al dataset {dataset_id}...")
    
    try:
        jwt_service = JWTService()
        auth_headers = jwt_service.get_auth_headers("data-harvester")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{DATA_STORAGE_URL}/datasets/{dataset_id}",
                headers=auth_headers
            )
            
            if response.status_code == 200:
                dataset = response.json()
                print(f"✅ Dataset accedido exitosamente")
                print(f"   ID: {dataset.get('id')}")
                print(f"   Nombre: {dataset.get('name')}")
                print(f"   Filas: {dataset.get('row_count', 0)}")
                return True
            elif response.status_code == 404:
                print(f"❌ Dataset no encontrado: {response.status_code}")
                return False
            elif response.status_code == 403:
                print(f"❌ Sin permisos para acceder al dataset: {response.status_code}")
                return False
            else:
                print(f"⚠️ Respuesta inesperada: {response.status_code}")
                print(f"   Respuesta: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Error accediendo al dataset: {str(e)}")
        return False

async def main():
    """Función principal de pruebas."""
    print("🧪 Iniciando pruebas de autenticación JWT")
    print("=" * 50)
    
    # Prueba 1: Autenticación básica
    auth_ok = await test_jwt_authentication()
    
    if not auth_ok:
        print("\n❌ La autenticación JWT no está funcionando")
        print("   Verifica que:")
        print("   1. El data-storage esté ejecutándose en el puerto 8003")
        print("   2. Las variables JWT_SECRET y JWT_ALGORITHM estén configuradas")
        print("   3. El middleware de autenticación esté habilitado")
        return
    
    # Prueba 2: Crear dataset de prueba
    dataset_id = await test_dataset_creation()
    
    if dataset_id:
        # Prueba 3: Acceder al dataset creado
        access_ok = await test_dataset_access(dataset_id)
        
        if access_ok:
            print(f"\n🎉 ¡Todas las pruebas pasaron exitosamente!")
            print(f"✅ Dataset de prueba creado: {dataset_id}")
            print(f"   Puedes usar este ID en tus pruebas de integración")
        else:
            print(f"\n⚠️ Dataset creado pero hay problemas de acceso")
    else:
        print(f"\n⚠️ Autenticación funciona pero no se pudo crear dataset")
        print(f"   Esto puede ser normal si el middleware está deshabilitado")

if __name__ == "__main__":
    asyncio.run(main()) 