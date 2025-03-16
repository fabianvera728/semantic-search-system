# API Gateway

Este servicio actúa como punto de entrada único para todos los servicios del sistema de búsqueda semántica, redirigiendo las solicitudes al servicio correspondiente.

## Características

- Proxy inverso para todos los servicios del sistema
- Enrutamiento basado en prefijos de URL
- Manejo de errores y timeouts
- Configuración mediante variables de entorno

## Arquitectura

El API Gateway sigue una arquitectura de proxy inverso, donde todas las solicitudes entrantes son redirigidas al servicio correspondiente según el prefijo de la URL:

- `/auth/*` -> Servicio de autenticación
- `/data-harvester/*` -> Servicio de recolección de datos
- `/data-processor/*` -> Servicio de procesamiento de datos
- `/embedding-service/*` -> Servicio de embeddings
- `/search-service/*` -> Servicio de búsqueda

## Configuración

La configuración se realiza mediante variables de entorno:

- `API_GATEWAY_HOST`: Host del servidor (por defecto: "0.0.0.0").
- `API_GATEWAY_PORT`: Puerto del servidor (por defecto: 8000).
- `AUTH_SERVICE_URL`: URL del servicio de autenticación (por defecto: "http://auth-service:8001").
- `DATA_HARVESTER_URL`: URL del servicio de recolección de datos (por defecto: "http://data-harvester:8002").
- `DATA_PROCESSOR_URL`: URL del servicio de procesamiento de datos (por defecto: "http://data-processor:8003").
- `EMBEDDING_SERVICE_URL`: URL del servicio de embeddings (por defecto: "http://embedding-service:8004").
- `SEARCH_SERVICE_URL`: URL del servicio de búsqueda (por defecto: "http://search-service:8005").

## Ejecución

### Con Docker

```bash
docker build -t api-gateway .
docker run -p 8000:8000 api-gateway
```

### Sin Docker

```bash
pip install -r requirements.txt
python main.py
```

## Uso

Para acceder a un servicio específico, utiliza el prefijo correspondiente en la URL:

- Autenticación: `http://localhost:8000/auth/...`
- Recolección de datos: `http://localhost:8000/data-harvester/...`
- Procesamiento de datos: `http://localhost:8000/data-processor/...`
- Embeddings: `http://localhost:8000/embedding-service/...`
- Búsqueda: `http://localhost:8000/search-service/...`

Por ejemplo, para registrar un usuario:

```
POST http://localhost:8000/auth/register
```

Para obtener información sobre los datasets:

```
GET http://localhost:8000/data-harvester/datasets
``` 