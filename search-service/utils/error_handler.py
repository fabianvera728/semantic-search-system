from fastapi import Request
from fastapi.responses import JSONResponse
from typing import Dict, Any

class ErrorHandler:
    """Handler for API errors."""
    
    @staticmethod
    async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
        """Handle ValueError exceptions."""
        return JSONResponse(
            status_code=400,
            content={
                "error": "Bad Request",
                "message": str(exc),
                "type": "ValueError"
            }
        )
    
    @staticmethod
    async def key_error_handler(request: Request, exc: KeyError) -> JSONResponse:
        """Handle KeyError exceptions."""
        return JSONResponse(
            status_code=400,
            content={
                "error": "Bad Request",
                "message": f"Missing required field: {str(exc)}",
                "type": "KeyError"
            }
        )
    
    @staticmethod
    async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle general exceptions."""
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "message": str(exc),
                "type": type(exc).__name__
            }
        ) 