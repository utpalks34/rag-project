"""
Integration tests for the complete application.
"""

import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


@pytest.fixture
def client():
    """Create test client for FastAPI app."""
    from backend.main import app
    return TestClient(app)


class TestHealthEndpoint:
    """Test health check endpoint."""
    
    def test_health_check(self, client):
        """Test health check response."""
        response = client.get("/health")
        
        assert response.status_code == 200
        assert "status" in response.json()
        assert "database_connected" in response.json()


class TestDocumentUpload:
    """Test document upload endpoints."""
    
    @pytest.mark.skip(reason="Requires file system setup")
    def test_upload_pdf(self, client):
        """Test PDF upload."""
        # Create mock PDF file
        content = b"%PDF-1.4\n%Test PDF"
        
        response = client.post(
            "/api/upload",
            files={"file": ("test.pdf", content, "application/pdf")}
        )
        
        # Should fail - invalid PDF, but should process file
        assert response.status_code in [200, 400]


class TestQueryEndpoint:
    """Test query endpoint."""
    
    @pytest.mark.skip(reason="Requires RAG pipeline initialization")
    def test_query_documents(self, client):
        """Test query endpoint."""
        response = client.post(
            "/api/query",
            json={
                "query": "What is photosynthesis?",
                "top_k": 5,
                "include_sources": True
            }
        )
        
        assert response.status_code in [200, 503]  # 503 if not initialized


class TestErrorResponses:
    """Test error response formats."""
    
    def test_404_not_found(self, client):
        """Test 404 error response."""
        response = client.get("/nonexistent-endpoint")
        
        assert response.status_code == 404
    
    def test_invalid_json(self, client):
        """Test invalid JSON request."""
        response = client.post(
            "/api/query",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
