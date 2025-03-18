import logging
import json
import asyncio
from typing import Dict, Any, List, Callable, Awaitable
from fastapi import FastAPI
from uuid import UUID
import aio_pika
from abc import ABC, abstractmethod
from datetime import datetime, date

from ...config import AppConfig
from ...contexts.embedding.application import (
    get_command_handlers,
    ProcessDatasetRowsRequestDTO,
    CreateDatasetRequestDTO
)

logger = logging.getLogger(__name__)


# Función para convertir cadenas a objetos nativos cuando sea posible
def parse_json_values(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Procesa valores en un diccionario JSON para convertir cadenas a objetos nativos
    cuando sea posible (UUID, datetime, etc.)
    """
    if not isinstance(data, dict):
        return data
    
    result = {}
    for key, value in data.items():
        # Si es un diccionario anidado, procesarlo recursivamente
        if isinstance(value, dict):
            result[key] = parse_json_values(value)
        # Si es una lista, procesar cada elemento
        elif isinstance(value, list):
            result[key] = [
                parse_json_values(item) if isinstance(item, dict) else item
                for item in value
            ]
        # Si es una cadena, intentar convertirla a objetos nativos
        elif isinstance(value, str):
            # Intentar convertir a UUID
            try:
                if len(value) == 36 and '-' in value:  # Formato típico de UUID
                    result[key] = UUID(value)
                    continue
            except ValueError:
                pass
            
            # Intentar convertir a datetime (formato ISO)
            try:
                if 'T' in value and ('+' in value or 'Z' in value or '-' in value[10:]):
                    result[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                    continue
            except ValueError:
                pass
            
            # Si no se pudo convertir, mantener el valor original
            result[key] = value
        else:
            # Mantener otros tipos de valores sin cambios
            result[key] = value
    
    return result


async def handle_dataset_created_event(event_data: Dict[str, Any]) -> None:
    """
    Manejador para el evento dataset.created
    Crea un dataset en el embedding-service y procesa sus filas iniciales
    """
    try:
        # Procesar los valores del evento para convertir cadenas a objetos nativos
        event_data = parse_json_values(event_data)
        
        dataset_id = event_data.get('dataset_id')
        logger.info(f"[✅] Handling dataset.created event for dataset {dataset_id}")
        logger.debug(f"Event data: {json.dumps(event_data, default=str)}")
        
        # Si el dataset_id es un string que parece un UUID, convertirlo a UUID
        if isinstance(dataset_id, str):
            try:
                dataset_id = UUID(dataset_id)
                logger.info(f"Converted dataset_id string to UUID: {dataset_id}")
                event_data['dataset_id'] = dataset_id
            except ValueError:
                logger.warning(f"dataset_id {dataset_id} is not a valid UUID, using as string")
        
        # Obtener el command handler
        command_handlers = get_command_handlers()
        
        # Crear el dataset en el embedding-service
        create_request = CreateDatasetRequestDTO(
            dataset_id=event_data.get('dataset_id'),
            name=event_data.get('name', f"Dataset {event_data.get('dataset_id')}")
        )
        
        logger.info(f"Creating dataset with ID: {event_data.get('dataset_id')} (type: {type(event_data.get('dataset_id')).__name__})")
        create_result = await command_handlers.create_dataset_controller.execute(create_request.dict())
        
        if not create_result.success:
            logger.error(f"Failed to create dataset: {create_result.error}")
            return
        
        logger.info(f"Dataset created successfully, now processing rows...")
        # Procesar las filas del dataset
        process_request = ProcessDatasetRowsRequestDTO(
            dataset_id=event_data.get('dataset_id')
        )
        
        process_result = await command_handlers.process_dataset_rows_controller.execute(process_request.dict())
        
        if not process_result.success:
            logger.error(f"Failed to process dataset rows: {process_result.error}")
            return
            
        logger.info(f"✅ Successfully processed dataset {event_data.get('dataset_id')} from event")
        
    except Exception as e:
        logger.exception(f"Error handling dataset.created event: {str(e)}")


async def handle_dataset_rows_added_event(event_data: Dict[str, Any]) -> None:
    """
    Manejador para el evento dataset.rows_added
    Procesa las nuevas filas añadidas al dataset
    """
    try:
        # Procesar los valores del evento para convertir cadenas a objetos nativos
        event_data = parse_json_values(event_data)
        
        dataset_id = event_data.get('dataset_id')
        logger.info(f"[✅] Handling dataset.rows_added event for dataset {dataset_id}")
        logger.debug(f"Event data: {json.dumps(event_data, default=str)}")
        
        # Si el dataset_id es un string que parece un UUID, convertirlo a UUID
        if isinstance(dataset_id, str):
            try:
                dataset_id = UUID(dataset_id)
                logger.info(f"Converted dataset_id string to UUID: {dataset_id}")
                event_data['dataset_id'] = dataset_id
            except ValueError:
                logger.warning(f"dataset_id {dataset_id} is not a valid UUID, using as string")
        
        # Obtener el command handler
        command_handlers = get_command_handlers()
        
        # Procesar las filas del dataset
        process_request = ProcessDatasetRowsRequestDTO(
            dataset_id=dataset_id
        )
        
        logger.info(f"Processing rows for dataset ID: {dataset_id} (type: {type(dataset_id).__name__})")
        process_result = await command_handlers.process_dataset_rows_controller.execute(process_request.dict())
        
        if not process_result.success:
            logger.error(f"Failed to process dataset rows: {process_result.error}")
            return
            
        logger.info(f"✅ Successfully processed rows for dataset {dataset_id} from event")
        
    except Exception as e:
        logger.exception(f"Error handling dataset.rows_added event: {str(e)}")


# Definir la interfaz abstracta para los consumidores de eventos
class EventConsumer(ABC):
    """
    Interfaz abstracta para consumidores de eventos.
    Permite implementar diferentes tipos de consumidores (HTTP, RabbitMQ, Kafka, etc.)
    """
    
    @abstractmethod
    async def setup(self, app: FastAPI, event_handlers: Dict[str, Callable[[Dict[str, Any]], Awaitable[None]]]) -> None:
        """Configura el consumidor de eventos"""
        pass
    
    @abstractmethod
    async def start(self) -> None:
        """Inicia el consumo de eventos"""
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """Detiene el consumo de eventos"""
        pass


class HttpEventConsumer(EventConsumer):
    """
    Implementación de EventConsumer que utiliza endpoints HTTP para recibir eventos.
    """
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.event_handlers = {}
        
    async def setup(self, app: FastAPI, event_handlers: Dict[str, Callable[[Dict[str, Any]], Awaitable[None]]]) -> None:
        """Configura el endpoint HTTP para recibir eventos"""
        self.event_handlers = event_handlers
        
        @app.post("/api/v1/events")
        async def receive_event(event_data: Dict[str, Any]):
            """
            Endpoint que recibe eventos desde data-storage
            """
            event_type = event_data.get('event_type')
            
            if not event_type:
                logger.error("Received event with no event_type")
                return {"status": "error", "message": "Missing event_type"}
            
            logger.info(f"Received event of type: {event_type}")
            
            # Procesar valores JSON para convertir strings a objetos nativos
            processed_data = parse_json_values(event_data)
            
            # Buscar el manejador para este tipo de evento
            handler = self.event_handlers.get(event_type)
            
            if not handler:
                logger.warning(f"No handler registered for event type: {event_type}")
                return {"status": "ignored", "message": f"No handler for event type {event_type}"}
            
            # Ejecutar el manejador
            try:
                await handler(processed_data)
                return {"status": "success", "message": f"Event {event_type} processed successfully"}
            except Exception as e:
                logger.exception(f"Error processing event {event_type}: {str(e)}")
                return {"status": "error", "message": str(e)}
    
    async def start(self) -> None:
        """
        No se necesita iniciar nada específicamente para el consumidor HTTP
        ya que FastAPI maneja los endpoints
        """
        logger.info("HTTP event consumer ready to receive events")
    
    async def stop(self) -> None:
        """
        No se necesita detener nada específicamente para el consumidor HTTP
        """
        pass


class RabbitMQEventConsumer(EventConsumer):
    """
    Implementación de EventConsumer que utiliza RabbitMQ para recibir eventos.
    Utiliza un exchange de tipo topic y se suscribe a eventos específicos.
    """
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.rabbitmq_url = config.rabbitmq_url
        self.exchange_name = config.rabbitmq_exchange
        self.queue_name = config.rabbitmq_queue
        self.connection = None
        self.channel = None
        self.exchange = None
        self.queue = None
        self.consumer_tag = None
        self.event_handlers = {}
        logger.info(f"Initialized RabbitMQ consumer with URL: {self.rabbitmq_url}, Exchange: {self.exchange_name}, Queue: {self.queue_name}")
        
    async def setup(self, app: FastAPI, event_handlers: Dict[str, Callable[[Dict[str, Any]], Awaitable[None]]]) -> None:
        """Configura el consumidor de RabbitMQ"""
        self.event_handlers = event_handlers
        logger.info(f"Setting up RabbitMQ consumer with {len(event_handlers)} event handlers")
        
        for event_type, handler in event_handlers.items():
            logger.info(f"Registered handler for event type: {event_type}")
        
        # Registrar eventos de inicio y cierre de la aplicación
        @app.on_event("startup")
        async def start_rabbitmq_consumer():
            await self.start()
        
        @app.on_event("shutdown")
        async def stop_rabbitmq_consumer():
            await self.stop()
    
    async def start(self) -> None:
        """Inicia la conexión con RabbitMQ y comienza a consumir eventos"""
        try:
            logger.info(f"Connecting to RabbitMQ at {self.rabbitmq_url}...")
            
            # Establecer conexión con reintentos
            max_retries = 5
            retry_delay = 5  # segundos
            
            for attempt in range(1, max_retries + 1):
                try:
                    # Establecer conexión
                    self.connection = await aio_pika.connect_robust(self.rabbitmq_url)
                    logger.info("Successfully connected to RabbitMQ")
                    break
                except Exception as e:
                    if attempt < max_retries:
                        logger.warning(f"Failed to connect to RabbitMQ (attempt {attempt}/{max_retries}): {str(e)}")
                        await asyncio.sleep(retry_delay)
                    else:
                        logger.error(f"Failed to connect to RabbitMQ after {max_retries} attempts: {str(e)}")
                        raise
            
            # Crear canal
            self.channel = await self.connection.channel()
            logger.info("Created RabbitMQ channel")
            
            # Declarar exchange
            self.exchange = await self.channel.declare_exchange(
                self.exchange_name,
                aio_pika.ExchangeType.TOPIC,
                durable=True
            )
            logger.info(f"Declared RabbitMQ exchange: {self.exchange_name}")
            
            # Declarar cola
            self.queue = await self.channel.declare_queue(
                self.queue_name,
                durable=True
            )
            logger.info(f"Declared RabbitMQ queue: {self.queue_name}")
            
            # Enlazar la cola a todos los eventos que nos interesan
            for event_type in self.event_handlers.keys():
                await self.queue.bind(self.exchange, routing_key=event_type)
                logger.info(f"Subscribed to event: {event_type}")
            
            # Comenzar a consumir mensajes
            self.consumer_tag = await self.queue.consume(self._process_message)
            
            logger.info(f"✅ RabbitMQ consumer started, listening for events on queue {self.queue_name}")
            
        except Exception as e:
            logger.error(f"Error starting RabbitMQ consumer: {str(e)}")
            # Intentar limpiar recursos en caso de error
            await self.stop()
            raise
    
    async def stop(self) -> None:
        """Detiene el consumo de eventos y cierra la conexión con RabbitMQ"""
        try:
            if self.channel and self.consumer_tag:
                logger.info(f"Cancelling consumer with tag: {self.consumer_tag}")
                await self.channel.cancel(self.consumer_tag)
                self.consumer_tag = None
            
            if self.connection:
                logger.info("Closing RabbitMQ connection")
                await self.connection.close()
                self.connection = None
                self.channel = None
                self.exchange = None
                self.queue = None
                
            logger.info("RabbitMQ consumer stopped")
        except Exception as e:
            logger.error(f"Error stopping RabbitMQ consumer: {str(e)}")
    
    async def _process_message(self, message: aio_pika.IncomingMessage) -> None:
        """Procesa un mensaje recibido de RabbitMQ"""
        async with message.process():
            try:
                # Obtener el tipo de evento desde la routing key
                event_type = message.routing_key
                
                # Decodificar el cuerpo del mensaje
                body = message.body.decode()
                logger.info(f"📨 Received raw message: {body[:200]}...")
                
                # Decodificar JSON y procesar sus valores
                raw_event_data = json.loads(body)
                event_data = parse_json_values(raw_event_data)
                
                logger.info(f"📨 Received event from RabbitMQ: {event_type} - ID: {event_data.get('event_id', 'N/A')}")
                
                # Obtener el manejador para este tipo de evento
                handler = self.event_handlers.get(event_type)
                
                if not handler:
                    logger.warning(f"No handler registered for event type: {event_type}")
                    return
                
                # Ejecutar el manejador
                logger.info(f"Processing event {event_type} with handler: {handler.__name__}")
                await handler(event_data)
                logger.info(f"✅ Event {event_type} processed successfully")
                
            except json.JSONDecodeError as je:
                logger.error(f"Received invalid JSON in message body: {str(je)}")
                logger.error(f"Raw message body: {message.body.decode()[:500]}")
            except Exception as e:
                logger.exception(f"Error processing RabbitMQ message: {str(e)}")


def create_event_consumer(config: AppConfig) -> EventConsumer:
    """
    Factory method que crea el consumidor de eventos adecuado según la configuración.
    """
    consumer_type = config.event_consumer_type.lower()
    logger.info(f"Creating event consumer of type: {consumer_type}")
    
    if consumer_type == "rabbitmq":
        return RabbitMQEventConsumer(config)
    elif consumer_type == "http":
        return HttpEventConsumer(config)
    else:
        raise ValueError(f"Event consumer type not supported: {consumer_type}. Use 'rabbitmq' or 'http'.")


def setup_event_consumers(app: FastAPI) -> None:
    """
    Configura los consumidores de eventos según la configuración.
    """
    from ...config import get_app_config
    config = get_app_config()
    
    if not config.event_consumer_enabled:
        logger.info("Event consumer is disabled")
        return
    
    logger.info("Setting up event consumers...")
    
    # Mapa de manejadores de eventos
    event_handlers = {
        "dataset.created": handle_dataset_created_event,
        "dataset.rows_added": handle_dataset_rows_added_event
    }
    
    try:
        # Crear el consumidor de eventos apropiado
        consumer = create_event_consumer(config)
        
        # Configurar el consumidor
        asyncio.create_task(consumer.setup(app, event_handlers))
        
        consumer_type = config.event_consumer_type
        logger.info(f"✅ Event consumer ({consumer_type}) set up successfully")
    except Exception as e:
        logger.error(f"Error setting up event consumer: {str(e)}") 