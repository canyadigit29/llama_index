"""
Enhanced Error Handling Module for FastAPI application.

This module provides improved error handling and logging
capabilities for the LlamaIndex + Supabase integration.
"""

from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import traceback
import logging
import os
import json
import time
from typing import Callable, Dict, Any, Optional

# Configure logging
ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")
DEBUG = os.environ.get("DEBUG", "").lower() in ("true", "1", "yes")

logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)

logger = logging.getLogger("llama_index_backend")

class EnhancedJSONResponse(JSONResponse):
    """Enhanced JSON response with metadata."""
    
    def __init__(self, content: Dict[str, Any], status_code: int = 200, **kwargs):
        # Add metadata to all responses
        if isinstance(content, dict):
            content["metadata"] = {
                "timestamp": time.time(),
                "environment": ENVIRONMENT,
                "version": "1.0.0",
            }
        super().__init__(content=content, status_code=status_code, **kwargs)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for consistent error handling across the application.
    
    This middleware captures exceptions, logs them appropriately,
    and returns well-structured error responses.
    """
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        try:
            # Process the request
            response = await call_next(request)
            
            # Add processing time header
            process_time = time.time() - start_time
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            # Log the exception with stack trace
            logger.error(f"Unhandled exception: {str(e)}")
            logger.debug(traceback.format_exc())
            
            # Create a consistent error response
            error_detail = str(e) if DEBUG else "Internal server error"
            
            error_response = {
                "status": "error",
                "error": {
                    "type": type(e).__name__,
                    "message": error_detail,
                }
            }
            
            if DEBUG:
                error_response["error"]["detail"] = traceback.format_exc()
            
            # Return JSON response
            return EnhancedJSONResponse(
                content=error_response,
                status_code=500
            )


def add_error_handling(app: FastAPI) -> None:
    """
    Add error handling middleware to the FastAPI application.
    
    Args:
        app: The FastAPI application
    """
    app.add_middleware(ErrorHandlingMiddleware)
    
    # Override default JSONResponse with enhanced version
    app.add_middleware(
        BaseHTTPMiddleware,
        dispatch=wrap_responses
    )

async def wrap_responses(request: Request, call_next: Callable) -> JSONResponse:
    """Middleware to wrap all JSON responses with the enhanced response."""
    response = await call_next(request)
    
    # Only process JSON responses
    if response.headers.get("content-type") == "application/json":
        try:
            # Get the original response content
            body = b""
            async for chunk in response.body_iterator:
                body += chunk
            
            # Parse the content
            content = json.loads(body.decode())
            
            # Create an enhanced response
            return EnhancedJSONResponse(
                content=content,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
        except Exception as e:
            logger.error(f"Error enhancing response: {str(e)}")
    
    # Return original response for non-JSON responses
    return response
