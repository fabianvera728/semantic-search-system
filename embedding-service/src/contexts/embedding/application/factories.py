from typing import Optional, Dict, Any

from .commands import CommandHandlers
from .service_factory import get_service_factory, create_embedding_service


def create_command_handlers() -> CommandHandlers:
    """
    Create and return a new instance of CommandHandlers.
    
    Returns:
        A new instance of CommandHandlers with the embedding service injected.
    """
    embedding_service = create_embedding_service()
    return CommandHandlers(embedding_service)


# Singleton instance of command handlers
_command_handlers: Optional[CommandHandlers] = None


def get_command_handlers() -> CommandHandlers:
    """
    Get the singleton instance of CommandHandlers.
    
    Returns:
        The singleton instance of CommandHandlers.
    """
    global _command_handlers
    if _command_handlers is None:
        _command_handlers = create_command_handlers()
    return _command_handlers 