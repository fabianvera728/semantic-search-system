# Sistema de Búsqueda Semántica

Este sistema proporciona capacidades de búsqueda semántica para diferentes fuentes de datos, permitiendo encontrar información relevante basada en el significado y no solo en coincidencias exactas de palabras clave.

## Arquitectura

El sistema sigue una arquitectura de microservicios, donde cada servicio tiene una responsabilidad específica:

### Servicios

1. **Auth Service**: Proporciona autenticación y autorización para el sistema.
2. **Data Harvester**: Recolecta datos de diferentes fuentes (archivos, APIs, web).
3. **Data Processor**: Procesa y limpia los datos recolectados.
4. **Embedding Service**: Genera embeddings vectoriales para los datos procesados.
5. **Search Service**: Implementa la búsqueda semántica sobre los embeddings.
6. **Orchestrator (API Gateway)**: Actúa como punto de entrada único para todos los servicios.
7. **Frontend**: Interfaz de usuario para interactuar con el sistema.

## Diagrama de Arquitectura

```
+------------+     +----------------+     +----------------+
|            |     |                |     |                |
|  Frontend  +---->+  Orchestrator  +---->+  Auth Service  |
|            |     |  (API Gateway) |     |                |
+------------+     +-------+--------+     +----------------+
                           |
                           |
          +----------------+----------------+
          |                |                |
          v                v                v
+------------------+ +-------------+ +----------------+
|                  | |             | |                |
| Data Harvester   | | Data        | | Search Service |
|                  | | Processor   | |                |
+--------+---------+ +------+------+ +--------+-------+
         |                  |                 |
         |                  v                 |
         |         +----------------+         |
         +-------->+                +<--------+
                   | Embedding      |
                   | Service        |
                   |                |
                   +----------------+
```

## Ejecución

### Requisitos

- Docker
- Docker Compose

### Pasos

1. Clonar el repositorio:

```bash
git clone https://github.com/tu-usuario/semantic-search-system.git
cd semantic-search-system
```

2. Iniciar los servicios:

```bash
docker-compose up -d
```

3. Acceder a la interfaz web:

```
http://localhost:3000
```

## Servicios y Puertos

- **Orchestrator (API Gateway)**: http://localhost:8000
- **Frontend**: http://localhost:3000

## Acceso a los Servicios

Todos los servicios son accesibles a través del API Gateway (Orchestrator) utilizando los siguientes prefijos:

- **Auth Service**: http://localhost:8000/auth/...
- **Data Harvester**: http://localhost:8000/data-harvester/...
- **Data Processor**: http://localhost:8000/data-processor/...
- **Embedding Service**: http://localhost:8000/embedding-service/...
- **Search Service**: http://localhost:8000/search-service/...

## Configuración

Cada servicio puede configurarse mediante variables de entorno. Consulta el README.md de cada servicio para más detalles.

## Desarrollo

Para desarrollar un servicio específico, puedes ejecutar solo ese servicio:

```bash
docker-compose up -d orchestrator auth-service
```

## Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo LICENSE para más detalles. 