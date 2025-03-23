import logging
import asyncio
from typing import Dict, List, Any, Callable, Awaitable, Type, Set, Optional
import uuid
from datetime import datetime


logger = logging.getLogger(__name__)

DomainEvent = Any  # Se usará tipado dinámico para evitar la importación circular

class EventBus:
    """
    Event bus que maneja la publicación y suscripción a eventos de dominio.
    Sigue el patrón singleton para asegurar una única instancia en la aplicación.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EventBus, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._subscribers: Dict[str, List[Callable[[DomainEvent], Awaitable[None]]]] = {}
        self._message_broker: Optional["MessageBroker"] = None
        self._initialized = True
        logger.info("Event bus initialized")
    
    def set_message_broker(self, message_broker: "MessageBroker") -> None:
        """Configura el message broker para publicar eventos externos"""
        self._message_broker = message_broker
        
    async def publish(self, event: DomainEvent) -> None:
        """
        Publica un evento a todos los suscriptores internos y al message broker externo
        si está configurado.
        """
        event_type = event.event_type
        logger.info(f"[✅] Publishing event: {event_type}")
        
        # Notificar a suscriptores internos
        if event_type in self._subscribers:
            tasks = [
                subscriber(event) 
                for subscriber in self._subscribers[event_type]
            ]
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
        
        # Publicar al message broker si está disponible
        if self._message_broker:
            try:
                await self._message_broker.publish(event)
            except Exception as e:
                logger.error(f"[❌] Error publishing event to message broker: {str(e)}")
    
    def subscribe(self, event_type: str, subscriber: Callable[[DomainEvent], Awaitable[None]]) -> None:
        """Suscribe una función a un tipo específico de evento"""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        
        if subscriber not in self._subscribers[event_type]:
            self._subscribers[event_type].append(subscriber)
            logger.info(f"Subscriber added for event: {event_type}")
    
    def unsubscribe(self, event_type: str, subscriber: Callable[[DomainEvent], Awaitable[None]]) -> None:
        """Cancela la suscripción de una función a un tipo específico de evento"""
        if event_type in self._subscribers and subscriber in self._subscribers[event_type]:
            self._subscribers[event_type].remove(subscriber)
            logger.info(f"Subscriber removed for event: {event_type}")


# Singleton instance
_event_bus = None

def get_event_bus() -> EventBus:
    """Obtiene la instancia singleton del event bus"""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus 