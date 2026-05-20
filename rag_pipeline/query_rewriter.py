"""
Query processing and rewriting for improved retrieval.
Implements query enhancement and rewriting strategies.
"""

from typing import List, Optional
from utils.logger import logger


class QueryRewriter:
    """
    Rewrite and enhance queries for better retrieval.
    Implements various query expansion strategies.
    """
    
    def __init__(self, enable_rewriting: bool = True):
        """
        Initialize query rewriter.
        
        Args:
            enable_rewriting: Whether to enable query rewriting
        """
        self.enable_rewriting = enable_rewriting
    
    def rewrite_query(self, query: str) -> List[str]:
        """
        Generate multiple query variations for better retrieval.
        
        Args:
            query: Original query
            
        Returns:
            List of query variations
        """
        if not self.enable_rewriting:
            return [query]
        
        try:
            variations = [query]  # Always include original
            
            # Add question to statement form
            if query.endswith('?'):
                statement = query[:-1].strip()
                variations.append(statement)
            
            # Add common synonyms/expansions
            expanded = self._expand_query(query)
            variations.extend(expanded)
            
            # Remove duplicates
            variations = list(set(variations))
            
            logger.info(f"Generated {len(variations)} query variations")
            return variations
            
        except Exception as e:
            logger.error(f"Error rewriting query: {str(e)}")
            return [query]
    
    def _expand_query(self, query: str) -> List[str]:
        """
        Expand query with related terms.
        
        Args:
            query: Original query
            
        Returns:
            List of expanded queries
        """
        expansions = []
        
        # Common expansions
        query_lower = query.lower()
        
        # Define term synonyms/related terms
        related_terms = {
            'what': ['how', 'why', 'explain'],
            'how': ['method', 'process', 'steps'],
            'why': ['reason', 'cause', 'because'],
            'define': ['explain', 'meaning', 'definition'],
            'example': ['instance', 'case', 'sample'],
        }
        
        # Create variations with related terms
        for term, related in related_terms.items():
            if term in query_lower:
                for related_term in related:
                    variation = query_lower.replace(term, related_term)
                    expansions.append(variation)
        
        return expansions
    
    def extract_keywords(self, query: str, top_n: int = 5) -> List[str]:
        """
        Extract important keywords from query.
        
        Args:
            query: Query text
            top_n: Number of keywords to extract
            
        Returns:
            List of keywords
        """
        # Simple keyword extraction (non-stopwords)
        stopwords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at',
            'to', 'for', 'of', 'with', 'by', 'from', 'is', 'are',
            'be', 'was', 'were', 'what', 'how', 'why', 'who', 'where',
        }
        
        words = query.lower().split()
        keywords = [w for w in words if w not in stopwords and len(w) > 3]
        
        return keywords[:top_n]
    
    def construct_search_query(self, query: str, use_variations: bool = True) -> str:
        """
        Construct optimized search query.
        
        Args:
            query: User query
            use_variations: Whether to use query variations
            
        Returns:
            Optimized search query
        """
        if not use_variations:
            return query
        
        variations = self.rewrite_query(query)
        # For semantic search, we'll return the original
        # In advanced implementations, this could use OR operators
        return variations[0] if variations else query
