import os
import logging
import httpx
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.background import BackgroundTask
import uvicorn

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("api-gateway")

app = FastAPI(
    title="API Gateway",
    description="API Gateway para el sistema de búsqueda semántica - Solo Proxy",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# URLs de los servicios
SERVICE_URLS = {
    "auth": os.getenv("AUTH_SERVICE_URL", "http://auth-service:8001"),
    "data-harvester": os.getenv("DATA_HARVESTER_URL", "http://data-harvester:8002"),
    "data-storage": os.getenv("DATA_STORAGE_URL", "http://data-storage:8003"),
    "data-processor": os.getenv("DATA_PROCESSOR_URL", "http://data-processor:8004"),
    "embedding-service": os.getenv("EMBEDDING_SERVICE_URL", "http://embedding-service:8005"),
    "search-service": os.getenv("SEARCH_SERVICE_URL", "http://search-service:8006")
}

http_client = httpx.AsyncClient(timeout=30.0)

@app.on_event("shutdown")
async def shutdown_event():
    """Cierra el cliente HTTP al apagar la aplicación."""
    await http_client.aclose()

@app.get("/")
async def root():
    return {
        "message": "API Gateway - Sistema de Búsqueda Semántica",
        "version": "2.0.0",
        "services": list(SERVICE_URLS.keys())
    }

@app.get("/health")
async def health_check():
    """Verificar el estado de todos los servicios."""
    health_status = {"gateway": "healthy", "services": {}}
    
    for service_name, service_url in SERVICE_URLS.items():
        try:
            response = await http_client.get(f"{service_url}/", timeout=5.0)
            health_status["services"][service_name] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "url": service_url
            }
        except Exception as e:
            health_status["services"][service_name] = {
                "status": "unreachable",
                "url": service_url,
                "error": str(e)
            }
    
    return health_status

async def proxy_request(service_name: str, path: str, request: Request) -> Response:
    """
    Función genérica para proxificar requests a los servicios.
    
    Args:
        service_name: Nombre del servicio
        path: Path de la request
        request: Request original
        
    Returns:
        Response del servicio
    """
    if service_name not in SERVICE_URLS:
        raise HTTPException(status_code=404, detail=f"Service {service_name} not found")
    
    service_url = SERVICE_URLS[service_name]
    target_url = f"{service_url}{path}"
    
    # Obtener headers (excluir algunos que pueden causar problemas)
    headers = dict(request.headers)
    headers.pop("host", None) 
    headers.pop("content-length", None)
    
    # Obtener query parameters
    query_params = str(request.url.query)
    if query_params:
        target_url += f"?{query_params}"
    
    try:
        # Obtener el body si existe
        body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            body = await request.body()
    
        # Hacer la request al servicio
        response = await http_client.request(
            method=request.method,
            url=target_url,
            headers=headers,
            content=body,
            timeout=30.0
        )
        
        # Crear response
        response_headers = dict(response.headers)
        response_headers.pop("content-encoding", None)
        response_headers.pop("content-length", None)
        
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=response_headers
        )
        
    except httpx.TimeoutException:
        logger.error(f"Timeout calling {service_name} service at {target_url}")
        raise HTTPException(status_code=504, detail=f"Timeout calling {service_name} service")
    except httpx.RequestError as e:
        logger.error(f"Error calling {service_name} service: {str(e)}")
        raise HTTPException(status_code=502, detail=f"Error connecting to {service_name} service")
    except Exception as e:
        logger.error(f"Unexpected error proxying to {service_name}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# =====================================================
# RUTAS DE AUTENTICACIÓN (AUTH SERVICE)
# =====================================================

@app.api_route("/api/auth/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_auth(path: str, request: Request):
    """Proxy para el servicio de autenticación."""
    return await proxy_request("auth", f"/{path}", request)

# =====================================================
# RUTAS DE INTEGRACIÓN Y COSECHA (DATA HARVESTER)
# =====================================================
# Las rutas específicas se eliminaron para usar solo la ruta genérica /data-harvester/{path:path}

# =====================================================
# RUTAS DE ALMACENAMIENTO (DATA STORAGE)
# =====================================================

@app.api_route("/api/data/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_data_storage(path: str, request: Request):
    """Proxy para el servicio de almacenamiento de datos."""
    return await proxy_request("data-storage", f"/{path}", request)

# =====================================================
# RUTAS DE PROCESAMIENTO (DATA PROCESSOR)
# =====================================================

@app.api_route("/api/process/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_data_processor(path: str, request: Request):
    """Proxy para el servicio de procesamiento de datos."""
    return await proxy_request("data-processor", f"/{path}", request)

# =====================================================
# RUTAS DE EMBEDDINGS (EMBEDDING SERVICE)
# =====================================================

@app.api_route("/api/embeddings/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_embeddings(path: str, request: Request):
    """Proxy para el servicio de embeddings."""
    return await proxy_request("embedding-service", f"/{path}", request)

# =====================================================
# RUTAS DE BÚSQUEDA (SEARCH SERVICE)
# =====================================================

@app.api_route("/search/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_search(path: str, request: Request):
    """Proxy para el servicio de búsqueda."""
    return await proxy_request("search-service", f"/{path}", request)

# =====================================================
# RUTAS ESPECÍFICAS PARA COMPATIBILIDAD
# =====================================================

@app.api_route("/data-harvester/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_data_harvester_direct(path: str, request: Request):
    """Proxy directo para el data-harvester (compatibilidad)."""
    return await proxy_request("data-harvester", f"/{path}", request)

@app.api_route("/data-processor/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_data_processor_direct(path: str, request: Request):
    """Proxy directo para el data-processor (compatibilidad)."""
    return await proxy_request("data-processor", f"/{path}", request)

@app.api_route("/data-storage/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_data_storage_direct(path: str, request: Request):
    """Proxy directo para el data-storage (compatibilidad)."""
    return await proxy_request("data-storage", f"/{path}", request)

if __name__ == "__main__":
    port = int(os.getenv("API_GATEWAY_PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True) 