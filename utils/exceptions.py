"""
Exception handling and error utilities.
"""

from fastapi import HTTPException, status
from utils.logger import logger
from datetime import datetime
import uuid
from typing import Optional


class AIAssistantException(Exception):
    """Base exception for AI Assistant."""
    pass


class PDFProcessingError(AIAssistantException):
    """Error during PDF processing."""
    pass


class VectorStoreError(AIAssistantException):
    """Error with vector store operations."""
    pass


class RAGPipelineError(AIAssistantException):
    """Error in RAG pipeline."""
    pass


class OpenAIError(AIAssistantException):
    """Error with OpenAI API."""
    pass


def create_error_response(
    error_type: str,
    detail: str,
    status_code: int = 400,
    request_id: Optional[str] = None,
) -> HTTPException:
    """
    Create a standardized error response.
    
    Args:
        error_type: Type of error
        detail: Error details
        status_code: HTTP status code
        request_id: Request ID for tracking
        
    Returns:
        HTTPException with formatted response
    """
    request_id = request_id or str(uuid.uuid4())
    logger.error(f"[{request_id}] {error_type}: {detail}")
    
    return HTTPException(
        status_code=status_code,
        detail={
            "error": error_type,
            "detail": detail,
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id,
        },
    )


def handle_exception(exc: Exception, context: str = "") -> HTTPException:
    """
    Convert exceptions to HTTP responses.
    
    Args:
        exc: Exception to handle
        context: Context information
        
    Returns:
        HTTPException
    """
    request_id = str(uuid.uuid4())
    
    if isinstance(exc, PDFProcessingError):
        return create_error_response(
            "PDF_PROCESSING_ERROR",
            str(exc),
            status.HTTP_400_BAD_REQUEST,
            request_id,
        )
    
    elif isinstance(exc, VectorStoreError):
        logger.error(f"[{request_id}] Vector store error: {str(exc)}")
        return create_error_response(
            "VECTOR_STORE_ERROR",
            f"Vector store error: {str(exc)}",
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            request_id,
        )
    
    elif isinstance(exc, RAGPipelineError):
        logger.error(f"[{request_id}] RAG pipeline error: {str(exc)}")
        return create_error_response(
            "RAG_ERROR",
            str(exc),
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            request_id,
        )
    
    elif isinstance(exc, OpenAIError):
        logger.error(f"[{request_id}] OpenAI error: {str(exc)}")
        return create_error_response(
            "OPENAI_ERROR",
            "External API error. Please try again later.",
            status.HTTP_503_SERVICE_UNAVAILABLE,
            request_id,
        )
    
    else:
        logger.error(f"[{request_id}] Unexpected error: {str(exc)}")
        return create_error_response(
            "INTERNAL_ERROR",
            "An unexpected error occurred.",
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            request_id,
        )
