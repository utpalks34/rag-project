"""
Unit tests for RAG Pipeline.
Demonstrates testing structure and key test cases.
"""

import pytest
from unittest.mock import Mock, patch
from rag_pipeline.chunker import DocumentChunker
from rag_pipeline.query_rewriter import QueryRewriter
from vector_store.vector_db import VectorStore
from utils.pdf_processor import PDFProcessor
from utils.helpers import TextProcessor, ValidationUtils


class TestDocumentChunker:
    """Test document chunking functionality."""
    
    def test_chunk_text_basic(self):
        """Test basic text chunking."""
        chunker = DocumentChunker(chunk_size=100, chunk_overlap=10)
        
        text = "This is a test document. " * 20  # Long text
        chunks = chunker.chunk_text(text)
        
        assert len(chunks) > 1
        assert all('text' in chunk for chunk in chunks)
        assert all('chunk_index' in chunk for chunk in chunks)
    
    def test_chunk_with_metadata(self):
        """Test chunking with metadata preservation."""
        chunker = DocumentChunker()
        
        metadata = {"source_file": "test.pdf", "page_num": 1}
        chunks = chunker.chunk_text("Test text", metadata)
        
        assert all(chunk['metadata']['source_file'] == "test.pdf" for chunk in chunks)
    
    def test_chunk_pages(self):
        """Test chunking multiple pages."""
        chunker = DocumentChunker()
        
        pages = [
            {"text": "Page 1 content", "page_num": 1},
            {"text": "Page 2 content", "page_num": 2},
        ]
        
        chunks = chunker.chunk_document_pages(pages, "test.pdf")
        assert len(chunks) >= 2


class TestQueryRewriter:
    """Test query rewriting functionality."""
    
    def test_rewrite_query_basic(self):
        """Test basic query rewriting."""
        rewriter = QueryRewriter(enable_rewriting=True)
        
        query = "What is photosynthesis?"
        variations = rewriter.rewrite_query(query)
        
        assert len(variations) > 0
        assert query in variations[0]  # Original should be included
    
    def test_extract_keywords(self):
        """Test keyword extraction."""
        rewriter = QueryRewriter()
        
        query = "What is the process of photosynthesis in plants?"
        keywords = rewriter.extract_keywords(query, top_n=3)
        
        assert len(keywords) <= 3
        assert all(isinstance(k, str) for k in keywords)


class TestTextProcessor:
    """Test text processing utilities."""
    
    def test_clean_text(self):
        """Test text cleaning."""
        text = "  This  is   a   test  with  spaces.  "
        cleaned = TextProcessor.clean_text(text)
        
        assert "  " not in cleaned  # No double spaces
        assert cleaned.strip() == cleaned
    
    def test_truncate_text(self):
        """Test text truncation."""
        text = "A" * 1000
        truncated = TextProcessor.truncate_text(text, max_length=100)
        
        assert len(truncated) <= 103  # 100 + "..."
        assert truncated.endswith("...")
    
    def test_extract_keywords(self):
        """Test keyword extraction."""
        text = "Machine learning is a subset of artificial intelligence"
        keywords = TextProcessor.extract_keywords(text, num_keywords=3)
        
        assert len(keywords) <= 3


class TestValidationUtils:
    """Test validation utilities."""
    
    def test_valid_pdf_file(self):
        """Test PDF file validation."""
        assert ValidationUtils.is_valid_pdf_file("document.pdf") is True
        assert ValidationUtils.is_valid_pdf_file("document.txt") is False
        assert ValidationUtils.is_valid_pdf_file("document.PDF") is True
    
    def test_valid_file_size(self):
        """Test file size validation."""
        # 10 MB
        assert ValidationUtils.is_valid_file_size(10 * 1024 * 1024, max_size_mb=50) is True
        
        # 60 MB (exceeds 50 MB limit)
        assert ValidationUtils.is_valid_file_size(60 * 1024 * 1024, max_size_mb=50) is False
    
    def test_validate_query(self):
        """Test query validation."""
        assert ValidationUtils.validate_query("What is photosynthesis?") is True
        assert ValidationUtils.validate_query("hi") is False
        assert ValidationUtils.validate_query("") is False


class TestRAGIntegration:
    """Integration tests for RAG pipeline."""
    
    @pytest.mark.skip(reason="Requires OpenAI API key")
    def test_end_to_end_rag(self):
        """Test complete RAG pipeline."""
        from rag_pipeline.pipeline import RAGPipeline
        
        rag = RAGPipeline()
        
        # Process document
        result = rag.process_document(
            text="Photosynthesis is the process...",
            filename="test.pdf"
        )
        
        assert result['chunks_created'] > 0
        
        # Answer question
        response = rag.answer_question("What is photosynthesis?")
        
        assert 'answer' in response
        assert len(response['answer']) > 0


class TestErrorHandling:
    """Test error handling."""
    
    def test_invalid_pdf_processing(self):
        """Test handling of invalid PDF."""
        from utils.exceptions import PDFProcessingError
        
        processor = PDFProcessor("/tmp")
        
        with pytest.raises(PDFProcessingError):
            processor.extract_text_from_pdf("/nonexistent/file.pdf")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
