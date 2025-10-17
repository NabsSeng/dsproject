"""
Cache service for storing and retrieving generated files by task ID.
"""

import os
import json
import hashlib
import logging
from typing import Dict, Optional, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class CacheService:
    """Service for caching generated files and metadata."""
    
    def __init__(self, cache_dir: str = "cache", ttl_hours: int = 24):
        """Initialize cache service.
        
        Args:
            cache_dir: Directory to store cache files
            ttl_hours: Time to live for cache entries in hours
        """
        self.cache_dir = cache_dir
        self.ttl = timedelta(hours=ttl_hours)
        self._ensure_cache_dir()
    
    def _ensure_cache_dir(self):
        """Ensure cache directory exists."""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
            logger.info(f"Created cache directory: {self.cache_dir}")
    
    def _get_cache_path(self, task_id: str) -> str:
        """Get cache file path for task ID."""
        return os.path.join(self.cache_dir, f"{task_id}.json")
    
    def _is_cache_valid(self, cache_data: Dict) -> bool:
        """Check if cache entry is still valid based on TTL."""
        created_at = datetime.fromisoformat(cache_data.get('created_at', ''))
        return datetime.now() - created_at < self.ttl
    
    def get(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached data for task ID.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Cached data dictionary or None if not found/expired
        """
        try:
            cache_path = self._get_cache_path(task_id)
            
            if not os.path.exists(cache_path):
                logger.debug(f"No cache found for task: {task_id}")
                return None
            
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            if not self._is_cache_valid(cache_data):
                logger.info(f"Cache expired for task: {task_id}")
                self.delete(task_id)
                return None
            
            logger.info(f"Cache hit for task: {task_id}")
            return cache_data.get('data')
            
        except Exception as e:
            logger.error(f"Error retrieving cache for task {task_id}: {str(e)}")
            return None
    
    def set(self, task_id: str, data: Dict[str, Any]) -> bool:
        """Store data in cache for task ID.
        
        Args:
            task_id: Task identifier
            data: Data to cache (should include 'files' and 'metadata')
            
        Returns:
            True if successful, False otherwise
        """
        try:
            cache_path = self._get_cache_path(task_id)
            
            cache_entry = {
                'task_id': task_id,
                'created_at': datetime.now().isoformat(),
                'data': data
            }
            
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_entry, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Cached data for task: {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error caching data for task {task_id}: {str(e)}")
            return False
    
    def delete(self, task_id: str) -> bool:
        """Delete cached data for task ID.
        
        Args:
            task_id: Task identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            cache_path = self._get_cache_path(task_id)
            
            if os.path.exists(cache_path):
                os.remove(cache_path)
                logger.info(f"Deleted cache for task: {task_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting cache for task {task_id}: {str(e)}")
            return False
    
    def clear_expired(self) -> int:
        """Clear all expired cache entries.
        
        Returns:
            Number of entries cleared
        """
        cleared_count = 0
        
        try:
            for filename in os.listdir(self.cache_dir):
                if not filename.endswith('.json'):
                    continue
                
                cache_path = os.path.join(self.cache_dir, filename)
                
                try:
                    with open(cache_path, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)
                    
                    if not self._is_cache_valid(cache_data):
                        os.remove(cache_path)
                        cleared_count += 1
                        
                except Exception as e:
                    logger.error(f"Error processing cache file {filename}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error clearing expired cache: {str(e)}")
        
        if cleared_count > 0:
            logger.info(f"Cleared {cleared_count} expired cache entries")
        
        return cleared_count
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get cache statistics and information.
        
        Returns:
            Dictionary with cache statistics
        """
        try:
            files = [f for f in os.listdir(self.cache_dir) if f.endswith('.json')]
            total_entries = len(files)
            
            valid_entries = 0
            expired_entries = 0
            total_size = 0
            
            for filename in files:
                cache_path = os.path.join(self.cache_dir, filename)
                total_size += os.path.getsize(cache_path)
                
                try:
                    with open(cache_path, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)
                    
                    if self._is_cache_valid(cache_data):
                        valid_entries += 1
                    else:
                        expired_entries += 1
                        
                except Exception:
                    expired_entries += 1
            
            return {
                'total_entries': total_entries,
                'valid_entries': valid_entries,
                'expired_entries': expired_entries,
                'total_size_bytes': total_size,
                'cache_dir': self.cache_dir,
                'ttl_hours': self.ttl.total_seconds() / 3600
            }
            
        except Exception as e:
            logger.error(f"Error getting cache info: {str(e)}")
            return {}

# Global cache instance
cache_service = CacheService(
    cache_dir=os.getenv('CACHE_DIR', 'cache'),
    ttl_hours=int(os.getenv('CACHE_TTL_HOURS', '24'))
)