"""
Configuration management for the AI Study Notes Assistant.
Handles environment variables and application settings.
"""

from pydantic_settings import BaseSettings
from typing import List, Optional
from pathlib import Path
import os


class Settings(BaseSettings):
    """Main application settings."""
    
    # OpenAI Configuration
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4")
    openai_embedding_model: str = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    
    # Backend Configuration
    backend_host: str = os.getenv("BACKEND_HOST", "0.0.0.0")
    backend_port: int = int(os.getenv("BACKEND_PORT", 8000))
    backend_workers: int = int(os.getenv("BACKEND_WORKERS", 4))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Frontend Configuration
    frontend_port: int = int(os.getenv("FRONTEND_PORT", 8501))
    
    # Paths
    chroma_db_path: str = os.getenv("CHROMA_DB_PATH", "./data/chroma_db")
    upload_folder: str = os.getenv("UPLOAD_FOLDER", "./data/uploads")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./data/app.db")
    
    # RAG Configuration
    chunk_size: int = int(os.getenv("CHUNK_SIZE", 512))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", 50))
    top_k_results: int = int(os.getenv("TOP_K_RESULTS", 5))
    confidence_threshold: float = float(os.getenv("CONFIDENCE_THRESHOLD", 0.5))
    batch_size: int = int(os.getenv("BATCH_SIZE", 32))
    
    # Security
    secret_key: str = os.getenv("SECRET_KEY", "change-me-in-production")
    allowed_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:8501",
        "http://127.0.0.1:8501",
    ]
    
    # Features
    enable_query_rewriting: bool = os.getenv("ENABLE_QUERY_REWRITING", "true").lower() == "true"
    enable_hybrid_search: bool = os.getenv("ENABLE_HYBRID_SEARCH", "true").lower() == "true"
    enable_summarization: bool = os.getenv("ENABLE_SUMMARIZATION", "true").lower() == "true"
    max_upload_size_mb: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", 50))
    
    # Environment
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Cache
    enable_cache: bool = os.getenv("ENABLE_CACHE", "true").lower() == "true"
    cache_ttl: int = int(os.getenv("CACHE_TTL", 3600))
    
    # Rate Limiting
    rate_limit_per_minute: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", 60))
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create necessary directories
        Path(self.chroma_db_path).mkdir(parents=True, exist_ok=True)
        Path(self.upload_folder).mkdir(parents=True, exist_ok=True)


# Initialize global settings
settings = Settings()
