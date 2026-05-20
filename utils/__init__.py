"""
Initialize utils package.
"""

from utils.logger import logger
from utils.pdf_processor import PDFProcessor
from utils.exceptions import (
    AIAssistantException,
    PDFProcessingError,
    VectorStoreError,
    RAGPipelineError,
    OpenAIError,
    handle_exception,
)
from utils.models import (
    DocumentChunk,
    RAGResponse,
    QueryRequest,
    DocumentUploadResponse,
    ChatMessage,
    ChatHistoryResponse,
    HealthResponse,
    ErrorResponse,
)
from utils.helpers import TextProcessor, ValidationUtils, CacheUtils, MetricsTracker

__all__ = [
    "logger",
    "PDFProcessor",
    "AIAssistantException",
    "PDFProcessingError",
    "VectorStoreError",
    "RAGPipelineError",
    "OpenAIError",
    "handle_exception",
    "DocumentChunk",
    "RAGResponse",
    "QueryRequest",
    "DocumentUploadResponse",
    "ChatMessage",
    "ChatHistoryResponse",
    "HealthResponse",
    "ErrorResponse",
    "TextProcessor",
    "ValidationUtils",
    "CacheUtils",
    "MetricsTracker",
]
