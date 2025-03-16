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
    description="API Gateway para el sistema de búsqueda semántica",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

SERVICE_URLS = {
    "auth": os.getenv("AUTH_SERVICE_URL", "http://auth-service:8001"),
    "data-harvester": os.getenv("DATA_HARVESTER_URL", "http://data-harvester:8002"),
    "data-storage": os.getenv("DATA_STORAGE_URL", "http://data-storage:8003"),
    "data-processor": os.getenv("DATA_PROCESSOR_URL", "http://data-processor:8004"),
    "embedding-service": os.getenv("EMBEDDING_SERVICE_URL", "http://embedding-service:8005"),
    "search-service": os.getenv("SEARCH_SERVICE_URL", "http://search-service:8006")
}

http_client = httpx.AsyncClient()

@app.on_event("shutdown")
async def shutdown_event():
    """Cierra el cliente HTTP al apagar la aplicación."""
    await http_client.aclose()

@app.get("/")
async def root():
    """Endpoint raíz para verificar que el servicio está funcionando."""
    return {
        "message": "API Gateway is running",
        "services": {
            service: url for service, url in SERVICE_URLS.items()
        }
    }

@app.api_route("/api/auth/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"])
async def auth_proxy(request: Request, path: str):
    """Proxy para el servicio de autenticación."""
    return await proxy_request(request, "auth", path)

@app.api_route("/data-harvester/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"])
async def data_harvester_proxy(request: Request, path: str):
    """Proxy para el servicio de recolección de datos."""
    return await proxy_request(request, "data-harvester", path)

@app.api_route("/api/data/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"])
async def data_storage_proxy(request: Request, path: str):
    """Proxy para el servicio de almacenamiento de datos."""
    return await proxy_request(request, "data-storage", path)

@app.api_route("/data-processor/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"])
async def data_processor_proxy(request: Request, path: str):
    """Proxy para el servicio de procesamiento de datos."""
    return await proxy_request(request, "data-processor", path)

@app.api_route("/embedding-service/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"])
async def embedding_service_proxy(request: Request, path: str):
    """Proxy para el servicio de embeddings."""
    return await proxy_request(request, "embedding-service", path)

@app.api_route("/search-service/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"])
async def search_service_proxy(request: Request, path: str):
    """Proxy para el servicio de búsqueda."""
    return await proxy_request(request, "search-service", path)

async def proxy_request(request: Request, service: str, path: str):
    """
    Reenvía la solicitud al servicio correspondiente.
    
    Args:
        request: Solicitud original
        service: Nombre del servicio
        path: Ruta de la solicitud
        
    Returns:
        Respuesta del servicio
    """
    if service not in SERVICE_URLS:
        raise HTTPException(status_code=404, detail=f"Servicio '{service}' no encontrado")
    
    target_url = f"{SERVICE_URLS[service]}/{path}"
    
    method = request.method
    
    headers = dict(request.headers)
    headers.pop("host", None) 
    
    params = dict(request.query_params)
    body = await request.body()
    
    try:
        response = await http_client.request(
            method=method,
            url=target_url,
            headers=headers,
            params=params,
            content=body,
            timeout=30.0
        )
        
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers),
            background=BackgroundTask(response.aclose)
        )
    except httpx.RequestError as e:
        logger.error(f"Error al enviar solicitud a {target_url}: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Error al comunicarse con el servicio: {str(e)}")

if __name__ == "__main__":
    host = os.getenv("API_GATEWAY_HOST", "0.0.0.0")
    port = int(os.getenv("API_GATEWAY_PORT", "8000"))
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=False
    ) 