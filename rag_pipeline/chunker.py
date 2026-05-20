"""
Document chunking and splitting utilities for RAG pipeline.
Uses RecursiveCharacterTextSplitter for semantic chunking.
"""

from typing import List, Dict, Optional
from langchain_text_splitters import RecursiveCharacterTextSplitter
from utils.logger import logger


class DocumentChunker:
    """
    Handle document chunking with configurable parameters.
    Implements semantic chunking using RecursiveCharacterTextSplitter.
    """
    
    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        separators: Optional[List[str]] = None,
    ):
        """
        Initialize the document chunker.
        
        Args:
            chunk_size: Size of each chunk (characters)
            chunk_overlap: Overlap between chunks (characters)
            separators: List of separators to split on
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Default separators prioritize semantic boundaries
        if separators is None:
            separators = [
                "\n\n",  # Paragraph breaks
                "\n",    # Line breaks
                ". ",    # Sentence ends
                " ",     # Words
                "",      # Characters
            ]
        
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=separators,
            length_function=len,
        )
        
        logger.info(
            f"Initialized DocumentChunker: chunk_size={chunk_size}, "
            f"overlap={chunk_overlap}"
        )
    
    def chunk_text(
        self,
        text: str,
        metadata: Optional[Dict[str, any]] = None,
    ) -> List[Dict[str, any]]:
        """
        Split text into chunks with metadata.
        
        Args:
            text: Text to chunk
            metadata: Metadata to attach to chunks
            
        Returns:
            List of chunks with metadata
        """
        try:
            chunks = self.splitter.split_text(text)
            
            chunked_docs = []
            for i, chunk in enumerate(chunks):
                doc = {
                    "text": chunk,
                    "chunk_index": i,
                    "chunk_count": len(chunks),
                    "metadata": metadata or {},
                }
                chunked_docs.append(doc)
            
            logger.info(f"Chunked text into {len(chunks)} chunks")
            return chunked_docs
            
        except Exception as e:
            logger.error(f"Error chunking text: {str(e)}")
            raise
    
    def chunk_document_pages(
        self,
        pages: List[Dict[str, any]],
        source_file: str,
    ) -> List[Dict[str, any]]:
        """
        Chunk multiple pages of a document.
        
        Args:
            pages: List of page dictionaries with 'text' and 'page_num'
            source_file: Source filename
            
        Returns:
            List of chunks with page information
        """
        all_chunks = []
        
        for page in pages:
            metadata = {
                "source_file": source_file,
                "page_num": page.get("page_num", 0),
            }
            
            chunks = self.chunk_text(page.get("text", ""), metadata)
            all_chunks.extend(chunks)
        
        logger.info(
            f"Created {len(all_chunks)} chunks from "
            f"{len(pages)} pages of {source_file}"
        )
        return all_chunks
    
    def recalculate_chunk_params(
        self,
        text_length: int,
        target_chunks: int = 10,
    ) -> tuple:
        """
        Dynamically calculate chunk parameters based on text length.
        
        Args:
            text_length: Total length of text
            target_chunks: Target number of chunks
            
        Returns:
            Tuple of (chunk_size, chunk_overlap)
        """
        if target_chunks <= 0:
            target_chunks = 1
        
        chunk_size = max(self.chunk_size, text_length // target_chunks)
        chunk_overlap = max(0, chunk_size // 10)  # 10% overlap
        
        logger.info(
            f"Recalculated chunk params: size={chunk_size}, "
            f"overlap={chunk_overlap}"
        )
        
        return chunk_size, chunk_overlap
