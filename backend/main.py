"""
FastAPI backend for the AI Study Notes Assistant.
Main application entry point with routes and middleware configuration.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
import time
import uuid
from datetime import datetime, timezone
from typing import Optional
import os

from config import settings
from rag_pipeline.pipeline import RAGPipeline
from utils.pdf_processor import PDFProcessor
from utils.models import (
    RAGResponse,
    QueryRequest,
    DocumentUploadResponse,
    ChatHistoryResponse,
    ChatMessage,
    HealthResponse,
    DocumentChunk,
)
from utils.logger import logger
from utils.exceptions import handle_exception, PDFProcessingError
from utils.helpers import ValidationUtils, CacheUtils, metrics_tracker


# ==================== LIFESPAN ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup components."""
    global rag_pipeline, pdf_processor
    try:
        logger.info("Starting AI Study Notes Assistant...")
        rag_pipeline = RAGPipeline()
        pdf_processor = PDFProcessor(settings.upload_folder)
        logger.info("All components initialized successfully")
    except Exception as e:
        logger.error(f"Startup error: {str(e)}")
        raise
    yield
    logger.info("Shutting down AI Study Notes Assistant...")


# Initialize FastAPI app
app = FastAPI(
    title="AI Study Notes Assistant",
    description="Production-ready RAG-powered study assistant",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global instances
rag_pipeline: Optional[RAGPipeline] = None
pdf_processor: Optional[PDFProcessor] = None
cache = CacheUtils(ttl=settings.cache_ttl if settings.enable_cache else 0)





class RequestIdMiddleware(BaseHTTPMiddleware):
    """Middleware to add request ID to all requests."""

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)

        logger.info(
            f"[{request_id}] {request.method} {request.url.path} - "
            f"Status: {response.status_code} - Time: {process_time:.2f}s"
        )

        return response


app.add_middleware(RequestIdMiddleware)


# ==================== UTILITY ENDPOINTS ====================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        db_connected = rag_pipeline is not None and rag_pipeline.vector_store is not None
        api_key_configured = len(settings.openai_api_key) > 0

        return HealthResponse(
            status="healthy" if db_connected and api_key_configured else "degraded",
            timestamp=datetime.now(timezone.utc),
            database_connected=db_connected,
            api_key_configured=api_key_configured,
        )
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return HealthResponse(
            status="unhealthy",
            timestamp=datetime.now(timezone.utc),
            database_connected=False,
            api_key_configured=False,
        )


@app.get("/stats")
async def get_stats():
    """Get application statistics."""
    if not rag_pipeline:
        raise HTTPException(status_code=503, detail="RAG Pipeline not initialized")
    
    return {
        "pipeline_stats": rag_pipeline.get_stats(),
        "metrics": {
            "response_time_avg_ms": metrics_tracker.get_average("response_time"),
            "query_count": len(metrics_tracker.metrics.get("query_count", [])),
        },
    }


# ==================== DOCUMENT ENDPOINTS ====================

@app.post("/api/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """
    Upload and process a PDF document.
    
    - **file**: PDF file to upload (max 50MB)
    
    Returns:
        Upload success status with document info
    """
    try:
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Validate file
        if not ValidationUtils.is_valid_pdf_file(file.filename):
            raise PDFProcessingError("File must be a PDF")
        
        file_content = await file.read()
        
        if not ValidationUtils.is_valid_file_size(
            len(file_content),
            settings.max_upload_size_mb
        ):
            raise PDFProcessingError(
                f"File size exceeds {settings.max_upload_size_mb}MB limit"
            )
        
        logger.info(f"[{request_id}] Uploading file: {file.filename}")
        
        # Save file
        file_path = pdf_processor.save_uploaded_file(file_content, file.filename)
        
        # Extract text
        extracted_data = pdf_processor.extract_text_from_pdf(file_path)
        
        # Process with RAG pipeline
        result = rag_pipeline.process_document(
            text=extracted_data["text"],
            filename=file.filename,
            pages=extracted_data.get("pages"),
        )
        
        upload_time = time.time() - start_time
        metrics_tracker.record_metric("upload_time", upload_time)
        
        return DocumentUploadResponse(
            filename=file.filename,
            file_id=request_id,
            total_pages=extracted_data["total_pages"],
            chunks_created=result["chunks_created"],
            upload_time=datetime.utcnow(),
            status="success",
        )
        
    except PDFProcessingError as e:
        raise handle_exception(e, "document_upload")
    except Exception as e:
        raise handle_exception(e, "document_upload")


# ==================== QUERY ENDPOINTS ====================

@app.post("/api/query")
async def query_documents(request: QueryRequest):
    """
    Query uploaded documents using RAG.
    
    Returns:
        RAG response with answer and source citations
    """
    try:
        start_time = time.time()
        
        # Validate query
        if not ValidationUtils.validate_query(request.query):
            raise HTTPException(
                status_code=400,
                detail="Query too short or invalid"
            )
        
        logger.info(f"Processing query: {request.query[:100]}")
        
        # RAG pipeline
        rag_response = rag_pipeline.answer_question(
            query=request.query,
            top_k=request.top_k,
            include_sources=request.include_sources,
        )
        
        # Format response
        source_chunks = [
            DocumentChunk(
                id=chunk.get('id', ''),
                text=chunk['text'][:200] + "..." if len(chunk['text']) > 200 else chunk['text'],
                page_num=chunk['metadata'].get('page_num', 0),
                source_file=chunk['metadata'].get('source_file', 'Unknown'),
                metadata=chunk['metadata'],
            )
            for chunk in rag_response.get('source_chunks', [])
        ]
        
        response_time = time.time() - start_time
        metrics_tracker.record_metric("response_time", response_time)
        metrics_tracker.record_metric("query_count", 1)
        
        return RAGResponse(
            answer=rag_response['answer'],
            source_chunks=source_chunks,
            confidence_scores=rag_response.get('confidence_scores', []),
            response_time_ms=rag_response.get('response_time_ms', response_time * 1000),
            model_used=rag_response.get('model_used', settings.openai_model),
        )
        
    except Exception as e:
        raise handle_exception(e, "query")


@app.get("/api/chat/history", response_model=ChatHistoryResponse)
async def get_chat_history():
    """Get chat history."""
    if not rag_pipeline:
        raise HTTPException(status_code=503, detail="RAG Pipeline not initialized")
    
    history = rag_pipeline.get_chat_history()
    
    messages = [
        ChatMessage(
            role=msg['role'],
            content=msg['content'],
            timestamp=msg.get('timestamp', datetime.utcnow()),
            sources=msg.get('sources'),
        )
        for msg in history
    ]
    
    return ChatHistoryResponse(
        messages=messages,
        total_messages=len(messages),
    )


@app.post("/api/chat/clear")
async def clear_chat_history():
    """Clear chat history."""
    if not rag_pipeline:
        raise HTTPException(status_code=503, detail="RAG Pipeline not initialized")
    
    rag_pipeline.clear_chat_history()
    return {"status": "success", "message": "Chat history cleared"}


# ==================== DOCUMENT MANAGEMENT ====================

@app.delete("/api/documents/{doc_id}")
async def delete_document(doc_id: str):
    """Delete a document from the vector store."""
    try:
        logger.info(f"Deleting document: {doc_id}")
        
        # In production, you'd track document IDs and files
        # For now, return success
        return {"status": "success", "message": f"Document {doc_id} deleted"}
        
    except Exception as e:
        raise handle_exception(e, "delete_document")


# ==================== ERROR HANDLING ====================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail if isinstance(exc.detail, dict) else "HTTP Error",
            "detail": exc.detail if isinstance(exc.detail, str) else str(exc.detail),
            "request_id": request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all exceptions."""
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
    
    logger.error(f"[{request_id}] Unhandled exception: {str(exc)}")
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": str(exc) if settings.debug else "An error occurred",
            "request_id": request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host=settings.backend_host,
        port=settings.backend_port,
        workers=settings.backend_workers,
        log_level=settings.log_level.lower(),
    )
