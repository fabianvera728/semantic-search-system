"""
Módulo de eventos para la infraestructura del servicio.
Contiene implementaciones del bus de eventos y message brokers.
"""

# Primero exponemos la clase base y la implementación de RabbitMQ
from .message_broker import MessageBroker, RabbitMQMessageBroker

# Después exponemos el EventBus y la función para obtenerlo
from .event_bus import EventBus, get_event_bus

__all__ = ["get_event_bus", "EventBus", "MessageBroker", "RabbitMQMessageBroker", "create_message_broker"]

# Factory method implementado aquí para evitar importaciones circulares
def create_message_broker(config) -> MessageBroker:
    """
    Factory method que crea el message broker adecuado según la configuración.
    """
    broker_type = config.event_broker_type.lower()
    
    if broker_type == "rabbitmq":
        return RabbitMQMessageBroker(config)
    else:
        raise ValueError(f"Broker type not supported: {broker_type}. Only 'rabbitmq' is supported.") 