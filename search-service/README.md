# Search Service

Servicio de búsqueda semántica para el sistema de búsqueda semántica. Este servicio proporciona una API para realizar búsquedas semánticas en datasets, generar embeddings y gestionar modelos de embedding.

## Arquitectura

El servicio sigue los principios de Domain-Driven Design (DDD) y está organizado en las siguientes capas:

- **Domain**: Contiene las entidades, objetos de valor, excepciones y repositorios del dominio.
- **Application**: Contiene los servicios de aplicación que orquestan las operaciones del dominio.
- **Infrastructure**: Contiene las implementaciones concretas de los repositorios y servicios externos.
- **Apps**: Contiene las aplicaciones que exponen la funcionalidad del servicio, como la API REST.

## Estructura del proyecto

```
search-service/
├── src/
│   ├── apps/
│   │   └── api/
│   │       ├── __init__.py
│   │       ├── app.py
│   │       └── search_controller.py
│   ├── contexts/
│   │   └── search/
│   │       ├── __init__.py
│   │       ├── domain/
│   │       │   ├── __init__.py
│   │       │   ├── entities.py
│   │       │   ├── exceptions.py
│   │       │   ├── repositories.py
│   │       │   └── value_objects.py
│   │       ├── application/
│   │       │   ├── __init__.py
│   │       │   └── search_service.py
│   │       └── infrastructure/
│   │           ├── __init__.py
│   │           ├── embedding/
│   │           │   ├── __init__.py
│   │           │   ├── embedding_repository_impl.py
│   │           │   └── embedding_strategy.py
│   │           └── search_repository_impl.py
│   └── __init__.py
├── Dockerfile
├── requirements.txt
└── run.py
```

## Funcionalidades

- Búsqueda semántica en datasets
- Generación de embeddings para textos
- Gestión de modelos de embedding
- Soporte para diferentes tipos de búsqueda (semántica, híbrida, etc.)

## API

### Endpoints

- `POST /search`: Realiza una búsqueda en un dataset
- `POST /search/embeddings`: Genera embeddings para una lista de textos
- `GET /search/models`: Lista los modelos de embedding disponibles
- `GET /search/models/{model_name}`: Obtiene información sobre un modelo de embedding específico

## Ejecución

### Local

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar el servicio
python run.py
```

### Docker

```bash
# Construir la imagen
docker build -t search-service .

# Ejecutar el contenedor
docker run -p 8000:8000 search-service
```

## Configuración

El servicio se configura mediante variables de entorno:

- `HOST`: Host en el que se ejecutará el servicio (por defecto: 0.0.0.0)
- `PORT`: Puerto en el que se ejecutará el servicio (por defecto: 8000)
- `RELOAD`: Indica si se debe recargar el servicio al detectar cambios en el código (por defecto: False) 