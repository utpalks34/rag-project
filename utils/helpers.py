"""
Utility functions for the AI Study Notes Assistant.
"""

from typing import List, Dict, Optional
import re
from utils.logger import logger


class TextProcessor:
    """Text processing utilities."""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """
        Clean and normalize text.
        
        Args:
            text: Raw text
            
        Returns:
            Cleaned text
        """
        # Remove extra whitespace
        text = " ".join(text.split())
        # Remove special characters but keep essential punctuation
        text = re.sub(r'[^\w\s.!?,;:\'"()-]', '', text)
        return text
    
    @staticmethod
    def extract_keywords(text: str, num_keywords: int = 5) -> List[str]:
        """
        Extract keywords from text (simple implementation).
        
        Args:
            text: Input text
            num_keywords: Number of keywords to extract
            
        Returns:
            List of keywords
        """
        # Simple keyword extraction - words longer than 4 chars
        words = re.findall(r'\b\w{4,}\b', text.lower())
        # Count frequency
        freq = {}
        for word in words:
            freq[word] = freq.get(word, 0) + 1
        
        # Return top keywords
        keywords = sorted(freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, count in keywords[:num_keywords]]
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 500) -> str:
        """
        Truncate text to maximum length.
        
        Args:
            text: Input text
            max_length: Maximum length
            
        Returns:
            Truncated text
        """
        if len(text) > max_length:
            return text[:max_length] + "..."
        return text


class ValidationUtils:
    """Validation utilities."""
    
    @staticmethod
    def is_valid_pdf_file(filename: str) -> bool:
        """Check if file is valid PDF."""
        return filename.lower().endswith('.pdf')
    
    @staticmethod
    def is_valid_file_size(file_size: int, max_size_mb: int = 50) -> bool:
        """Check if file size is within limits."""
        max_bytes = max_size_mb * 1024 * 1024
        return file_size <= max_bytes
    
    @staticmethod
    def validate_query(query: str, min_length: int = 3) -> bool:
        """Validate user query."""
        return len(query.strip()) >= min_length


class CacheUtils:
    """Simple cache utilities."""
    
    def __init__(self, ttl: int = 3600):
        """
        Initialize cache.
        
        Args:
            ttl: Time to live in seconds
        """
        self.cache: Dict[str, Dict] = {}
        self.ttl = ttl
    
    def get(self, key: str) -> Optional[any]:
        """Get value from cache."""
        if key in self.cache:
            entry = self.cache[key]
            import time
            if time.time() - entry['time'] < self.ttl:
                return entry['value']
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, value: any):
        """Set value in cache."""
        import time
        self.cache[key] = {
            'value': value,
            'time': time.time()
        }
    
    def clear(self):
        """Clear cache."""
        self.cache.clear()


# Metric tracking utility
class MetricsTracker:
    """Track application metrics."""
    
    def __init__(self):
        self.metrics: Dict[str, List[float]] = {}
    
    def record_metric(self, name: str, value: float):
        """Record a metric."""
        if name not in self.metrics:
            self.metrics[name] = []
        self.metrics[name].append(value)
    
    def get_average(self, name: str) -> Optional[float]:
        """Get average of a metric."""
        if name in self.metrics and self.metrics[name]:
            return sum(self.metrics[name]) / len(self.metrics[name])
        return None
    
    def get_stats(self, name: str) -> Dict[str, float]:
        """Get statistics for a metric."""
        if name not in self.metrics or not self.metrics[name]:
            return {}
        
        values = self.metrics[name]
        return {
            'count': len(values),
            'min': min(values),
            'max': max(values),
            'avg': sum(values) / len(values),
        }


# Global instances
metrics_tracker = MetricsTracker()
cache_utils = CacheUtils()
