import logging
import json
from abc import ABC, abstractmethod
from typing import Dict, Any, TYPE_CHECKING
import aio_pika
from dataclasses import asdict
from uuid import UUID
from datetime import datetime, date, time

from ...config import AppConfig

# Evitamos la importación directa para romper el ciclo
# Si estamos haciendo comprobación de tipos, importamos DomainEvent; en runtime no importará
if TYPE_CHECKING:
    from ...contexts.dataset.domain.events import DomainEvent
else:
    # En runtime, usamos Any como tipo de DomainEvent para evitar la importación circular
    from typing import Any
    DomainEvent = Any

logger = logging.getLogger(__name__)


# Definimos un serializador personalizado para JSON que maneje tipos comunes no serializables
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        # UUID -> string
        if isinstance(obj, UUID):
            return str(obj)
        # datetime -> ISO format string
        elif isinstance(obj, datetime):
            return obj.isoformat()
        # date -> ISO format string
        elif isinstance(obj, date):
            return obj.isoformat()
        # time -> ISO format string
        elif isinstance(obj, time):
            return obj.isoformat()
        # set -> list
        elif isinstance(obj, set):
            return list(obj)
        # Cualquier otro tipo que no sea serializable de forma estándar
        try:
            # Para cualquier otro objeto, intentar convertirlo a dict si tiene el método __dict__
            return obj.__dict__
        except AttributeError:
            try:
                # O intentar representarlo como string
                return str(obj)
            except Exception:
                pass
        # Usar la serialización por defecto para otros tipos
        return json.JSONEncoder.default(self, obj)


class MessageBroker(ABC):
    """
    Interfaz abstracta para message brokers.
    Permite implementar diferentes tipos de brokers (Redis, RabbitMQ, HTTP, etc.)
    """
    
    @abstractmethod
    async def publish(self, event: "DomainEvent") -> None:
        """Publica un evento al broker de mensajes"""
        pass
    
    @abstractmethod
    async def connect(self) -> None:
        """Conecta al broker de mensajes"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Desconecta del broker de mensajes"""
        pass


class RabbitMQMessageBroker(MessageBroker):
    """
    Implementación de MessageBroker que usa RabbitMQ para publicar eventos.
    Implementa un patrón de publicación/suscripción (pub/sub) con exchanges de tipo 'topic'.
    """
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.rabbitmq_url = config.rabbitmq_url
        self.exchange_name = config.rabbitmq_exchange
        self.connection = None
        self.channel = None
        self.exchange = None
        logger.info(f"RabbitMQ Message Broker initialized with URL: {self.rabbitmq_url}")
    
    async def connect(self) -> None:
        """Establece la conexión con RabbitMQ y declara el exchange"""
        try:
            logger.info(f"Connecting to RabbitMQ at {self.rabbitmq_url}...")
            self.connection = await aio_pika.connect_robust(self.rabbitmq_url)
            self.channel = await self.connection.channel()
            
            # Declarar un exchange de tipo 'topic' para enrutamiento basado en patrones
            self.exchange = await self.channel.declare_exchange(
                self.exchange_name,
                aio_pika.ExchangeType.TOPIC,
                durable=True
            )
            
            logger.info("RabbitMQ Message Broker connected successfully")
        except Exception as e:
            logger.error(f"Error connecting to RabbitMQ: {str(e)}")
            raise
    
    async def disconnect(self) -> None:
        """Cierra la conexión con RabbitMQ"""
        if self.connection:
            logger.info("Disconnecting from RabbitMQ...")
            await self.connection.close()
            self.connection = None
            self.channel = None
            self.exchange = None
            logger.info("RabbitMQ Message Broker disconnected successfully")
    
    async def publish(self, event: "DomainEvent") -> None:
        """
        Publica un evento al exchange de RabbitMQ usando el tipo de evento como clave de enrutamiento.
        Ejemplo: 'dataset.created', 'dataset.updated', etc.
        """
        if not self.exchange:
            logger.info("Exchange not found. Connecting to RabbitMQ...")
            await self.connect()
        
        try:
            # Convertir el evento a un diccionario y luego a JSON
            event_data = asdict(event)
            
            # Usar el encoder personalizado para manejar todos los tipos de datos
            event_json = json.dumps(event_data, cls=CustomJSONEncoder)
            
            logger.info(f"📤 Publishing event {event.event_type} with ID: {event.event_id}")
            logger.debug(f"Event data: {event_json[:200]}...")
            
            # Crear un mensaje con el contenido JSON
            message = aio_pika.Message(
                body=event_json.encode(),
                content_type="application/json",
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT  # Mensajes persistentes para mayor fiabilidad
            )
            
            # Publicar el mensaje con la clave de enrutamiento igual al tipo de evento
            routing_key = event.event_type
            await self.exchange.publish(message, routing_key=routing_key)
            
            logger.info(f"✅ Event {event.event_type} with ID {event.event_id} published successfully to exchange {self.exchange_name} with routing key {routing_key}")
        except Exception as e:
            logger.error(f"❌ Error publishing event to RabbitMQ: {str(e)}")
            # Intentar reconectar en caso de error
            logger.info("Attempting to reconnect to RabbitMQ...")
            await self.disconnect()
            await self.connect()
            # No reintentamos publicar aquí para evitar bucles infinitos 