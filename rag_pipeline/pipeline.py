"""
Main RAG Pipeline orchestrating the entire retrieval-augmented generation process.
Coordinates document processing, vector storage, retrieval, and LLM generation.
"""

import time
import uuid
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import hashlib

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage

from rag_pipeline.chunker import DocumentChunker
from vector_store.vector_db import VectorStore
from rag_pipeline.query_rewriter import QueryRewriter
from utils.logger import logger
from utils.exceptions import RAGPipelineError, OpenAIError
from config import settings


class RAGPipeline:
    """
    Complete RAG pipeline for question answering from documents.
    Handles embedding, storage, retrieval, and generation.
    """
    
    def __init__(self):
        """Initialize RAG pipeline with all components."""
        try:
            # Initialize embeddings
            self.embeddings = OpenAIEmbeddings(
                openai_api_key=settings.openai_api_key,
                model=settings.openai_embedding_model,
            )
            
            # Initialize LLM
            self.llm = ChatOpenAI(
                api_key=settings.openai_api_key,
                model=settings.openai_model,
                temperature=0.7,
            )
            
            # Initialize components
            self.chunker = DocumentChunker(
                chunk_size=settings.chunk_size,
                chunk_overlap=settings.chunk_overlap,
            )
            
            self.vector_store = VectorStore(
                db_path=settings.chroma_db_path,
                embedding_function=self.embeddings,
            )
            
            self.query_rewriter = QueryRewriter(
                enable_rewriting=settings.enable_query_rewriting,
            )
            
            # Chat history storage
            self.chat_history = []
            
            logger.info("RAG Pipeline initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing RAG Pipeline: {str(e)}")
            raise RAGPipelineError(f"Failed to initialize RAG Pipeline: {str(e)}")
    
    def process_document(
        self,
        text: str,
        filename: str,
        pages: Optional[List[Dict]] = None,
    ) -> Dict[str, any]:
        """
        Process a document: chunk it and store embeddings.
        
        Args:
            text: Full document text
            filename: Source filename
            pages: List of page dictionaries
            
        Returns:
            Processing result with chunk count and IDs
        """
        try:
            logger.info(f"Processing document: {filename}")
            start_time = time.time()
            
            # Chunk document
            if pages:
                chunks = self.chunker.chunk_document_pages(pages, filename)
            else:
                chunks = self.chunker.chunk_text(
                    text,
                    metadata={"source_file": filename}
                )
            
            if not chunks:
                raise RAGPipelineError("No chunks generated from document")
            
            # Generate IDs for chunks
            # Use global_index (not per-page chunk_index) to avoid collisions
            # when multiple pages each reset chunk_index back to 0.
            doc_ids = []
            doc_texts = []
            doc_metadatas = []
            
            for global_index, chunk in enumerate(chunks):
                chunk_id = self._generate_chunk_id(filename, global_index, chunk['text'])
                doc_ids.append(chunk_id)
                doc_texts.append(chunk['text'])
                
                metadata = chunk['metadata'].copy()
                metadata['chunk_index'] = global_index
                doc_metadatas.append(metadata)
            
            # Add to vector store
            self.vector_store.add_documents(
                documents=doc_texts,
                metadatas=doc_metadatas,
                ids=doc_ids,
            )
            
            processing_time = time.time() - start_time
            
            result = {
                'filename': filename,
                'chunks_created': len(chunks),
                'processing_time_ms': processing_time * 1000,
                'status': 'success',
            }
            
            logger.info(f"Document processed: {len(chunks)} chunks in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Error processing document {filename}: {str(e)}")
            raise RAGPipelineError(f"Failed to process document: {str(e)}")
    
    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        use_hybrid: Optional[bool] = None,
    ) -> List[Dict[str, any]]:
        """
        Retrieve relevant documents using semantic search.
        
        Args:
            query: User query
            top_k: Number of results
            use_hybrid: Whether to use hybrid search
            
        Returns:
            List of relevant chunks with metadata
        """
        try:
            top_k = top_k or settings.top_k_results
            use_hybrid = use_hybrid if use_hybrid is not None else settings.enable_hybrid_search
            
            logger.info(f"Retrieving documents for query: {query[:100]}...")
            
            # Rewrite query
            optimized_query = self.query_rewriter.construct_search_query(query)
            
            # Search
            if use_hybrid:
                results = self.vector_store.hybrid_search(
                    query=optimized_query,
                    top_k=top_k,
                )
            else:
                results = self.vector_store.search(
                    query=optimized_query,
                    top_k=top_k,
                )
            
            logger.info(f"Retrieved {len(results)} documents")
            return results
            
        except Exception as e:
            logger.error(f"Error retrieving documents: {str(e)}")
            raise RAGPipelineError(f"Retrieval failed: {str(e)}")
    
    def generate_answer(
        self,
        query: str,
        context_chunks: List[Dict[str, any]],
        include_sources: bool = True,
    ) -> Tuple[str, List[Dict], List[float]]:
        """
        Generate answer using LLM with retrieved context.
        
        Args:
            query: User query
            context_chunks: Retrieved context chunks
            include_sources: Whether to include source information
            
        Returns:
            Tuple of (answer, source_chunks, confidence_scores)
        """
        try:
            # Prepare context
            context_text = "\n\n".join([
                f"[Source: {c['metadata'].get('source_file', 'Unknown')}, "
                f"Page {c['metadata'].get('page_num', '?')}]\n{c['text']}"
                for c in context_chunks
            ])
            
            # Prepare confidence scores
            confidence_scores = [c.get('similarity_score', 0) for c in context_chunks]
            
            # Create prompt
            system_prompt = SystemMessage(content="""You are an expert AI study assistant. 
Use the provided context to answer questions accurately and thoroughly.
If the context doesn't contain relevant information, say so.
Provide clear, well-structured answers with proper citations.""")
            
            user_message = HumanMessage(content=f"""Context from study materials:
{context_text}

---

Question: {query}

Please provide a comprehensive answer based on the context above.""")
            
            # Generate answer
            logger.info("Generating answer with LLM...")
            response = self.llm.invoke([system_prompt, user_message])
            
            answer = response.content
            
            # Add to chat history
            self.chat_history.append({
                'role': 'user',
                'content': query,
                'timestamp': datetime.utcnow(),
            })
            self.chat_history.append({
                'role': 'assistant',
                'content': answer,
                'timestamp': datetime.utcnow(),
                'sources': [c['metadata'].get('source_file') for c in context_chunks],
            })
            
            return answer, context_chunks, confidence_scores
            
        except Exception as e:
            logger.error(f"Error generating answer: {str(e)}")
            raise RAGPipelineError(f"Answer generation failed: {str(e)}")
    
    def answer_question(
        self,
        query: str,
        top_k: Optional[int] = None,
        include_sources: bool = True,
    ) -> Dict[str, any]:
        """
        Complete RAG pipeline: retrieve and generate answer.
        
        Args:
            query: User question
            top_k: Number of context chunks
            include_sources: Include source information
            
        Returns:
            Complete response with answer and metadata
        """
        try:
            start_time = time.time()
            logger.info(f"Answering question: {query}")
            
            # Retrieve
            retrieved_chunks = self.retrieve(query, top_k)
            
            # Filter by confidence threshold
            filtered_chunks = [
                c for c in retrieved_chunks
                if c.get('similarity_score', 0) >= settings.confidence_threshold
            ]
            
            if not filtered_chunks:
                return {
                    'answer': "I couldn't find relevant information in the uploaded materials to answer this question.",
                    'source_chunks': [],
                    'confidence_scores': [],
                    'response_time_ms': (time.time() - start_time) * 1000,
                    'model_used': settings.openai_model,
                }
            
            # Generate answer
            answer, sources, scores = self.generate_answer(
                query,
                filtered_chunks,
                include_sources,
            )
            
            response_time = (time.time() - start_time) * 1000
            
            return {
                'answer': answer,
                'source_chunks': sources,
                'confidence_scores': scores,
                'response_time_ms': response_time,
                'model_used': settings.openai_model,
            }
            
        except Exception as e:
            logger.error(f"Error answering question: {str(e)}")
            raise RAGPipelineError(f"Failed to answer question: {str(e)}")
    
    def get_chat_history(self) -> List[Dict]:
        """Get chat history."""
        return self.chat_history
    
    def clear_chat_history(self):
        """Clear chat history."""
        self.chat_history = []
        logger.info("Chat history cleared")
    
    def _generate_chunk_id(self, filename: str, chunk_index: int, text: str = "") -> str:
        """Generate unique ID for a chunk using filename + global index + text snippet."""
        # Include first 64 chars of text to prevent collisions when pages
        # share the same chunk_index (e.g. page1-chunk0 vs page2-chunk0).
        content = f"{filename}_{chunk_index}_{text[:64]}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get_stats(self) -> Dict[str, any]:
        """Get pipeline statistics."""
        return {
            'vector_store': self.vector_store.get_collection_stats(),
            'chat_history_length': len(self.chat_history),
            'chunk_size': settings.chunk_size,
            'chunk_overlap': settings.chunk_overlap,
        }
