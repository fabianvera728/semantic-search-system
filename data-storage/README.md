# Data Storage Service

Este servicio proporciona APIs para almacenar y recuperar datasets para el Sistema de Búsqueda Semántica.

## Arquitectura

El servicio sigue los principios de Domain-Driven Design (DDD) y Arquitectura Hexagonal:

- **Capa de Dominio**: Contiene la lógica de negocio central, entidades, objetos de valor e interfaces de repositorio.
- **Capa de Aplicación**: Contiene los servicios de aplicación que orquestan los objetos de dominio.
- **Capa de Infraestructura**: Contiene las implementaciones de las interfaces de repositorio.
- **Capa de API**: Contiene los controladores que exponen los servicios de aplicación a través de endpoints HTTP.

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
│       └── infrastructure/
│           ├── __init__.py
│           ├── memory_repository.py
│           └── mysql_repository.py
├── infrastructure/
│   └── db/
│       ├── __init__.py
│       └── init_db.py
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

### Ejecución Local

1. Clonar el repositorio
2. Navegar al directorio `data-storage`
3. Ejecutar `docker-compose up -d`
4. La API estará disponible en `http://localhost:8002`

### Variables de Entorno

- `MYSQL_HOST`: Host de MySQL (predeterminado: `localhost`)
- `MYSQL_PORT`: Puerto de MySQL (predeterminado: `3306`)
- `MYSQL_USER`: Usuario de MySQL (predeterminado: `root`)
- `MYSQL_PASSWORD`: Contraseña de MySQL (predeterminado: `password`)
- `MYSQL_DATABASE`: Nombre de la base de datos MySQL (predeterminado: `data_storage`)
- `USE_IN_MEMORY_DB`: Usar base de datos en memoria en lugar de MySQL (predeterminado: `false`)
- `CORS_ORIGINS`: Lista separada por comas de orígenes CORS permitidos (predeterminado: `*`)
- `HOST`: Host al que se vinculará el servidor (predeterminado: `0.0.0.0`)
- `PORT`: Puerto al que se vinculará el servidor (predeterminado: `8000`)

## Pruebas

Para ejecutar las pruebas:

```bash
# Usando base de datos en memoria para pruebas
export USE_IN_MEMORY_DB=true
pytest
``` 