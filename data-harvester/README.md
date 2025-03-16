# Data Harvester Service

Servicio para la cosecha de datos de diversas fuentes como archivos, APIs y sitios web. Este servicio forma parte del sistema de búsqueda semántica.

## Características

- Cosecha de datos desde múltiples fuentes:
  - Archivos (CSV, JSON, Excel, etc.)
  - APIs REST
  - Sitios web (web scraping)
- API REST para interactuar con el servicio
- Procesamiento asíncrono de trabajos de cosecha
- Monitoreo del estado de los trabajos
- Configuración flexible mediante variables de entorno

## Requisitos

- Python 3.8+
- Dependencias listadas en `requirements.txt`

## Instalación

1. Clonar el repositorio:
   ```
   git clone https://github.com/tu-usuario/semantic-search-system.git
   cd semantic-search-system/data-harvester
   ```

2. Crear un entorno virtual:
   ```
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. Instalar dependencias:
   ```
   pip install -r requirements.txt
   ```

4. Configurar variables de entorno (opcional):
   Crear un archivo `.env` en el directorio raíz con las siguientes variables:
   ```
   DATA_HARVESTER_HOST=0.0.0.0
   DATA_HARVESTER_PORT=8000
   DATA_HARVESTER_UPLOAD_DIR=./uploads
   DATA_HARVESTER_DATA_DIR=./data
   DATA_HARVESTER_LOG_LEVEL=INFO
   ```

## Uso

### Iniciar el servicio

```
python -m src.main
```

El servicio estará disponible en `http://localhost:8000`.

### Endpoints de la API

- `GET /`: Verificar que el servicio está funcionando
- `GET /sources`: Obtener fuentes de datos disponibles
- `POST /harvest`: Iniciar un trabajo de cosecha
- `POST /upload`: Subir un archivo para cosecha
- `GET /jobs/{job_id}`: Obtener el estado de un trabajo

### Ejemplos de uso

#### Iniciar un trabajo de cosecha desde una API

```bash
curl -X POST "http://localhost:8000/harvest" \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "api",
    "config": {
      "url": "https://api.ejemplo.com/datos",
      "method": "GET",
      "headers": {
        "Authorization": "Bearer token123"
      }
    }
  }'
```

#### Subir un archivo para cosecha

```bash
curl -X POST "http://localhost:8000/upload" \
  -F "file=@datos.csv" \
  -F "source_type=file"
```

#### Verificar el estado de un trabajo

```bash
curl -X GET "http://localhost:8000/jobs/job-123"
```

## Estructura del proyecto

```
data-harvester/
├── src/
│   ├── application/
│   │   ├── use_cases/
│   │   │   ├── create_harvest_job_use_case.py
│   │   │   ├── process_harvest_job_use_case.py
│   │   │   └── ...
│   ├── domain/
│   │   ├── entities/
│   │   │   ├── harvest_job.py
│   │   │   └── ...
│   │   ├── repositories/
│   │   │   ├── harvester_repository.py
│   │   │   └── ...
│   ├── infrastructure/
│   │   ├── adapters/
│   │   │   ├── controllers/
│   │   │   │   ├── fastapi_controller.py
│   │   │   │   └── ...
│   │   │   ├── harvesters/
│   │   │   │   ├── file_harvester_adapter.py
│   │   │   │   ├── api_harvester_adapter.py
│   │   │   │   └── ...
│   │   │   ├── repositories/
│   │   │   │   ├── in_memory_harvester_repository.py
│   │   │   │   └── ...
│   │   ├── config/
│   │   │   ├── app_config.py
│   │   │   └── ...
│   ├── main.py
├── tests/
│   ├── unit/
│   │   └── ...
│   ├── integration/
│   │   └── ...
├── requirements.txt
└── README.md
```

## Desarrollo

### Ejecutar pruebas

```
pytest
```

### Ejecutar en modo desarrollo

```
uvicorn src.main:create_app --reload
```

## Licencia

Este proyecto está licenciado bajo los términos de la licencia MIT. 