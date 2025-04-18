import uvicorn
import logging
import os
from typing import Optional

from src.application.use_cases.create_harvest_job_use_case import CreateHarvestJobUseCase
from src.application.use_cases.process_harvest_job_use_case import ProcessHarvestJobUseCase
from src.application.use_cases.get_job_status_use_case import GetJobStatusUseCase
from src.application.use_cases.get_available_sources_use_case import GetAvailableSourcesUseCase
from src.application.use_cases.upload_file_use_case import UploadFileUseCase

from src.infrastructure.adapters.controllers import FastAPIController
from src.infrastructure.adapters.harvesters import FileHarvesterAdapter, APIHarvesterAdapter, WebHarvesterAdapter
from src.infrastructure.adapters.repositories import InMemoryHarvesterRepository
from src.infrastructure.config import get_app_config
from src.domain.services.data_source_service import DataSourceService
from src.domain.services.harvester_service import HarvesterService
from src.infrastructure.adapters.notifications import ConsoleNotificationAdapter


def setup_logging(log_level: str, log_file: Optional[str] = None):
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        numeric_level = logging.INFO
    
    logging_config = {
        'level': numeric_level,
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    }
    
    if log_file:
        logging_config['filename'] = log_file
        logging_config['filemode'] = 'a'
    
    logging.basicConfig(**logging_config)


def create_app():
    """
    Crea y configura la aplicación.
    
    Returns:
        La aplicación FastAPI configurada
    """
    # Cargar configuración
    config = get_app_config()
    
    # Configurar logging
    setup_logging(config.log_level, config.log_file)
    
    # Crear directorios necesarios
    os.makedirs(config.upload_dir, exist_ok=True)
    os.makedirs(config.data_dir, exist_ok=True)
    
    # Inicializar repositorio
    repository = InMemoryHarvesterRepository()
    
    # Inicializar adaptadores de cosecha
    file_harvester = FileHarvesterAdapter()
    api_harvester = APIHarvesterAdapter()
    web_harvester = WebHarvesterAdapter()
    
    # Inicializar adaptador de notificaciones
    notifier = ConsoleNotificationAdapter()
    
    # Inicializar servicios del dominio
    data_source_service = DataSourceService()
    harvester_service = HarvesterService(
        file_harvester=file_harvester,
        api_harvester=api_harvester,
        web_harvester=web_harvester,
        repository=repository,
        notifier=notifier
    )
    
    # Inicializar casos de uso
    create_harvest_job_use_case = CreateHarvestJobUseCase(
        harvester_service=harvester_service,
        data_source_service=data_source_service
    )
    process_harvest_job_use_case = ProcessHarvestJobUseCase(
        harvester_service=harvester_service
    )
    get_job_status_use_case = GetJobStatusUseCase(repository)
    get_available_sources_use_case = GetAvailableSourcesUseCase(
        data_source_service=data_source_service
    )
    upload_file_use_case = UploadFileUseCase(
        harvester_service=harvester_service,
        upload_dir=config.upload_dir
    )
    
    # Inicializar controlador
    controller = FastAPIController(
        create_harvest_job_use_case=create_harvest_job_use_case,
        process_harvest_job_use_case=process_harvest_job_use_case,
        get_job_status_use_case=get_job_status_use_case,
        get_available_sources_use_case=get_available_sources_use_case,
        upload_file_use_case=upload_file_use_case
    )
    
    return controller.get_app()


def main():
    config = get_app_config()
    
    app = create_app()
    
    uvicorn.run(
        app,
        host=config.host,
        port=config.port,
        log_level=config.log_level.lower()
    )


if __name__ == "__main__":
    main() 