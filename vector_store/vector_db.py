"""
Vector store management using ChromaDB for persistent vector storage.
Handles embedding generation, storage, and retrieval.
"""

import os
from typing import List, Dict, Optional, Tuple
import chromadb
from chromadb import EmbeddingFunction, Embeddings
from chromadb.config import Settings as ChromaSettings
from utils.logger import logger
from utils.exceptions import VectorStoreError


class LangChainEmbeddingWrapper(EmbeddingFunction):
    """
    Wraps a LangChain embedding object (e.g. OpenAIEmbeddings) so it can
    be used as a native ChromaDB EmbeddingFunction, bypassing ChromaDB's
    built-in ONNX model download.
    """

    def __init__(self, langchain_embeddings):
        self._embedder = langchain_embeddings

    def __call__(self, input: List[str]) -> Embeddings:
        return self._embedder.embed_documents(input)


class VectorStore:
    """
    Manage vector storage and retrieval using ChromaDB.
    Handles embeddings, persistence, and similarity search.
    """
    
    def __init__(
        self,
        db_path: str,
        embedding_function=None,
        collection_name: str = "documents",
    ):
        """
        Initialize vector store.
        
        Args:
            db_path: Path to ChromaDB storage
            embedding_function: Function to generate embeddings
            collection_name: Name of the collection
        """
        self.db_path = db_path
        self.collection_name = collection_name
        
        try:
            # Create ChromaDB client with persistence
            os.makedirs(db_path, exist_ok=True)
            
            self.client = chromadb.PersistentClient(
                path=db_path,
            )

            # Use ChromaDB's local ONNX embedding model (all-MiniLM-L6-v2).
            # It is downloaded once and cached; subsequent runs are instant.
            # We intentionally do NOT use the passed-in OpenAI embedding_function
            # here because it requires a paid API quota. The LLM (OpenAI) is only
            # used for answer *generation*, not for embedding.
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            
            logger.info(f"Initialized VectorStore at {db_path}")
            logger.info(f"Collection: {collection_name}")
            
        except Exception as e:
            logger.error(f"Error initializing VectorStore: {str(e)}")
            raise VectorStoreError(f"Failed to initialize vector store: {str(e)}")
    
    def add_documents(
        self,
        documents: List[str],
        metadatas: List[Dict[str, any]],
        ids: List[str],
    ) -> bool:
        """
        Add documents to vector store.
        
        Args:
            documents: List of document texts
            metadatas: List of metadata dictionaries
            ids: List of document IDs
            
        Returns:
            Success status
        """
        try:
            if not documents or not ids or not metadatas:
                raise ValueError("Documents, IDs, and metadata are required")
            
            if not (len(documents) == len(ids) == len(metadatas)):
                raise ValueError("Documents, IDs, and metadata must have same length")
            
            # Upsert to collection (handles re-uploads of the same document gracefully)
            self.collection.upsert(
                documents=documents,
                metadatas=metadatas,
                ids=ids,
            )
            
            logger.info(f"Upserted {len(documents)} documents to vector store (new or updated)")
            return True
            
        except Exception as e:
            logger.error(f"Error adding documents: {str(e)}")
            raise VectorStoreError(f"Failed to add documents: {str(e)}")
    
    def search(
        self,
        query: str,
        top_k: int = 5,
    ) -> List[Dict[str, any]]:
        """
        Search similar documents using cosine similarity.
        
        Args:
            query: Query text
            top_k: Number of results to return
            
        Returns:
            List of matching documents with scores
        """
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k,
            )
            
            # Format results
            formatted_results = []
            if results and results['documents'] and len(results['documents']) > 0:
                for i, doc in enumerate(results['documents'][0]):
                    distance = results['distances'][0][i] if results['distances'] else 0
                    # Convert distance to similarity score (cosine similarity)
                    similarity = 1 - distance
                    
                    formatted_results.append({
                        'text': doc,
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'id': results['ids'][0][i] if results['ids'] else '',
                        'similarity_score': similarity,
                    })
            
            logger.info(f"Search query returned {len(formatted_results)} results")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching vector store: {str(e)}")
            raise VectorStoreError(f"Search failed: {str(e)}")
    
    def delete_collection(self, collection_name: Optional[str] = None) -> bool:
        """
        Delete a collection.
        
        Args:
            collection_name: Name of collection (uses default if not specified)
            
        Returns:
            Success status
        """
        try:
            col_name = collection_name or self.collection_name
            self.client.delete_collection(name=col_name)
            logger.info(f"Deleted collection: {col_name}")
            return True
        except Exception as e:
            logger.error(f"Error deleting collection: {str(e)}")
            return False
    
    def get_collection_stats(self) -> Dict[str, any]:
        """
        Get statistics about the collection.
        
        Returns:
            Statistics dictionary
        """
        try:
            count = self.collection.count()
            return {
                'collection_name': self.collection_name,
                'document_count': count,
                'db_path': self.db_path,
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {str(e)}")
            return {}
    
    def hybrid_search(
        self,
        query: str,
        top_k: int = 5,
        alpha: float = 0.7,
    ) -> List[Dict[str, any]]:
        """
        Hybrid search combining semantic and keyword search.
        
        Args:
            query: Query text
            top_k: Number of results
            alpha: Weight for semantic search (1-alpha for keyword)
            
        Returns:
            Ranked results
        """
        try:
            # Semantic search
            semantic_results = self.search(query, top_k * 2)
            
            # Simple keyword search (look for query terms in text)
            keyword_results = self._keyword_search(query, top_k * 2)
            
            # Combine and rank results
            combined = {}
            for result in semantic_results:
                doc_id = result['id']
                combined[doc_id] = {
                    **result,
                    'semantic_score': result['similarity_score'],
                    'keyword_score': 0,
                }
            
            for result in keyword_results:
                doc_id = result['id']
                if doc_id in combined:
                    combined[doc_id]['keyword_score'] = result['score']
                else:
                    combined[doc_id] = {
                        **result,
                        'semantic_score': 0,
                        'keyword_score': result['score'],
                    }
            
            # Calculate final score
            for doc_id in combined:
                semantic = combined[doc_id].get('semantic_score', 0)
                keyword = combined[doc_id].get('keyword_score', 0)
                combined[doc_id]['final_score'] = (alpha * semantic) + ((1 - alpha) * keyword)
            
            # Sort by final score
            ranked = sorted(combined.values(), key=lambda x: x['final_score'], reverse=True)
            return ranked[:top_k]
            
        except Exception as e:
            logger.error(f"Error in hybrid search: {str(e)}")
            return self.search(query, top_k)
    
    def _keyword_search(self, query: str, top_k: int) -> List[Dict[str, any]]:
        """
        Simple keyword-based search.
        
        Args:
            query: Query text
            top_k: Number of results
            
        Returns:
            List of matching documents
        """
        try:
            query_terms = set(query.lower().split())
            all_docs = self.collection.get()
            
            scored_docs = []
            for i, doc in enumerate(all_docs['documents']):
                doc_terms = set(doc.lower().split())
                overlap = len(query_terms & doc_terms)
                if overlap > 0:
                    score = overlap / len(query_terms)
                    scored_docs.append({
                        'text': doc,
                        'metadata': all_docs['metadatas'][i],
                        'id': all_docs['ids'][i],
                        'score': score,
                    })
            
            # Sort by score
            scored_docs.sort(key=lambda x: x['score'], reverse=True)
            return scored_docs[:top_k]
            
        except Exception as e:
            logger.error(f"Error in keyword search: {str(e)}")
            return []
