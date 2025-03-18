# Data Storage Service

Este servicio proporciona APIs para almacenar y recuperar datasets para el Sistema de Búsqueda Semántica.

## Arquitectura

El servicio sigue los principios de Domain-Driven Design (DDD) y Arquitectura Hexagonal:

- **Capa de Dominio**: Contiene la lógica de negocio central, entidades, objetos de valor e interfaces de repositorio.
- **Capa de Aplicación**: Contiene los servicios de aplicación que orquestan los objetos de dominio.
- **Capa de Infraestructura**: Contiene las implementaciones de las interfaces de repositorio.
- **Capa de API**: Contiene los controladores que exponen los servicios de aplicación a través de endpoints HTTP.

### Sistema de Eventos

El servicio implementa un sistema de eventos basado en Domain Events que permite:

- Publicar eventos cuando ocurren cambios importantes en el dominio
- Utiliza RabbitMQ como sistema de mensajería
- Desacopla completamente los servicios mediante comunicación asíncrona
- Implementa un patrón publish/subscribe con exchanges de tipo topic

## Estructura de Directorios

```
src/
├── apps/
│   └── api/
│       ├── __init__.py
│       └── dataset_controller.py
├── contexts/
│   └── dataset/
│       ├── __init__.py
│       ├── application/
│       │   ├── __init__.py
│       │   └── dataset_service.py
│       ├── domain/
│       │   ├── __init__.py
│       │   ├── entities.py
│       │   ├── exceptions.py
│       │   ├── repositories.py
│       │   └── value_objects.py
│       │   └── events.py
│       └── infrastructure/
│           ├── __init__.py
│           ├── memory_repository.py
│           └── mysql_repository.py
├── infrastructure/
│   ├── db/
│   │   ├── __init__.py
│   │   └── init_db.py
│   └── events/
│       ├── __init__.py
│       ├── event_bus.py
│       └── message_broker.py
├── __init__.py
└── main.py
```

## Endpoints de API

El servicio expone los siguientes endpoints de API:

- `GET /datasets`: Listar todos los datasets del usuario actual
- `GET /datasets/public`: Listar todos los datasets públicos
- `GET /datasets/{dataset_id}`: Obtener un dataset específico por ID
- `POST /datasets`: Crear un nuevo dataset
- `PUT /datasets/{dataset_id}`: Actualizar un dataset
- `DELETE /datasets/{dataset_id}`: Eliminar un dataset
- `POST /datasets/{dataset_id}/rows`: Agregar una fila a un dataset
- `POST /datasets/{dataset_id}/columns`: Agregar una columna a un dataset

## Desarrollo

### Prerrequisitos

- Python 3.10+
- Docker y Docker Compose
- MySQL 8.0+
- RabbitMQ 3.8+

### Ejecución Local

1. Clonar el repositorio
2. Navegar al directorio `data-storage`
3. Ejecutar `docker-compose up -d`
4. La API estará disponible en `http://localhost:8003`

### Variables de Entorno

#### Base de datos y servidor
- `MYSQL_HOST`: Host de MySQL (predeterminado: `localhost`)
- `MYSQL_PORT`: Puerto de MySQL (predeterminado: `3306`)
- `MYSQL_USER`: Usuario de MySQL (predeterminado: `root`)
- `MYSQL_PASSWORD`: Contraseña de MySQL (predeterminado: `password`)
- `MYSQL_DATABASE`: Nombre de la base de datos MySQL (predeterminado: `data_storage`)
- `USE_IN_MEMORY_DB`: Usar base de datos en memoria en lugar de MySQL (predeterminado: `false`)
- `DATA_STORAGE_ALLOWED_ORIGINS`: Lista separada por comas de orígenes CORS permitidos (predeterminado: `*`)
- `DATA_STORAGE_HOST`: Host al que se vinculará el servidor (predeterminado: `0.0.0.0`)
- `DATA_STORAGE_PORT`: Puerto al que se vinculará el servidor (predeterminado: `8003`)

#### URLs de servicios
- `EMBEDDING_SERVICE_URL`: URL del servicio de embeddings (predeterminado: `http://embedding-service:8005`)
- `AUTH_SERVICE_URL`: URL del servicio de autenticación (predeterminado: `http://auth-service:8001`)

#### Configuración de eventos
- `ENABLE_EVENT_PUBLISHING`: Habilitar la publicación de eventos (predeterminado: `true`)

#### Configuración de RabbitMQ
- `RABBITMQ_URL`: URL de conexión a RabbitMQ (predeterminado: `amqp://guest:guest@rabbitmq:5672/`)
- `RABBITMQ_EXCHANGE`: Exchange de RabbitMQ para eventos (predeterminado: `semantic_search_events`)

#### Configuración de logging
- `DATA_STORAGE_LOG_LEVEL`: Nivel de logging (predeterminado: `INFO`)
- `DATA_STORAGE_LOG_FILE`: Ruta al archivo de log (opcional)

## Pruebas

Para ejecutar las pruebas:

```bash
# Usando base de datos en memoria para pruebas
export USE_IN_MEMORY_DB=true
pytest
``` 