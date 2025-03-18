import logging
from typing import Any, Dict, List, Optional, TypeVar, Generic, Type, Callable, Awaitable, Union
from pydantic import BaseModel, ValidationError

from ..domain.exceptions import (
    EmbeddingServiceException,
    InvalidRequestError
)

logger = logging.getLogger(__name__)

# Type variables for the generic controller
T = TypeVar('T', bound=BaseModel)  # Input DTO type
U = TypeVar('U')  # Output type


class CommandResult:
    """Result of a command execution."""
    
    def __init__(
        self, 
        success: bool = True, 
        data: Any = None, 
        error: Optional[str] = None,
        status_code: int = 200
    ):
        self.success = success
        self.data = data
        self.error = error
        self.status_code = status_code
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the result to a dictionary."""
        result = {
            "success": self.success,
        }
        
        if self.data is not None:
            result["data"] = self.data
            
        if self.error:
            result["error"] = self.error
            
        return result


class CommandController(Generic[T, U]):
    """Generic controller for handling commands."""
    
    def __init__(
        self, 
        input_type: Type[T],
        handler: Callable[[T], Awaitable[U]]
    ):
        """
        Initialize a command controller.
        
        Args:
            input_type: The Pydantic model class for the input DTO
            handler: The async function that processes the command and returns a result
        """
        self.input_type = input_type
        self.handler = handler
    
    async def execute(self, data: Dict[str, Any]) -> CommandResult:
        """
        Execute the command with the given data.
        
        Args:
            data: The input data as a dictionary
            
        Returns:
            A CommandResult containing the execution result
        """
        try:
            # Validate and convert input to the DTO
            input_dto = self.input_type(**data)
            
            # Execute the handler
            result = await self.handler(input_dto)
            
            # Return successful result
            return CommandResult(success=True, data=result)
            
        except ValidationError as e:
            # Handle validation errors
            logger.warning(f"Validation error: {str(e)}")
            return CommandResult(
                success=False,
                error=f"Validation error: {str(e)}",
                status_code=400
            )
            
        except InvalidRequestError as e:
            # Handle invalid request errors
            logger.warning(f"Invalid request: {str(e)}")
            return CommandResult(
                success=False,
                error=str(e),
                status_code=400
            )
            
        except EmbeddingServiceException as e:
            # Handle domain exceptions
            logger.error(f"Domain error: {str(e)}")
            return CommandResult(
                success=False,
                error=str(e),
                status_code=e.status_code if hasattr(e, 'status_code') else 500
            )
            
        except Exception as e:
            # Handle unexpected errors
            logger.exception(f"Unexpected error: {str(e)}")
            return CommandResult(
                success=False,
                error=f"An unexpected error occurred: {str(e)}",
                status_code=500
            ) 