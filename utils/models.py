"""
Response models and data structures for API endpoints.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class DocumentChunk(BaseModel):
    """Represents a chunk of text from a document."""
    id: str
    text: str
    page_num: int
    source_file: str
    metadata: Dict[str, Any] = {}


class RAGResponse(BaseModel):
    """RAG pipeline response structure."""
    answer: str
    source_chunks: List[DocumentChunk]
    confidence_scores: List[float]
    response_time_ms: float
    model_used: str


class QueryRequest(BaseModel):
    """User query request."""
    query: str = Field(..., min_length=1, max_length=1000)
    top_k: Optional[int] = Field(5, ge=1, le=20)
    include_sources: bool = True


class DocumentUploadResponse(BaseModel):
    """Response after uploading a document."""
    filename: str
    file_id: str
    total_pages: int
    chunks_created: int
    upload_time: datetime
    status: str


class ChatMessage(BaseModel):
    """Chat message structure."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    sources: Optional[List[str]] = None


class ChatHistoryResponse(BaseModel):
    """Chat history response."""
    messages: List[ChatMessage]
    total_messages: int


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: datetime
    database_connected: bool
    api_key_configured: bool


class ErrorResponse(BaseModel):
    """Error response structure."""
    error: str
    detail: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None
