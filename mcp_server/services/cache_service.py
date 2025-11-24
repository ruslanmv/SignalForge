"""
Cache Service

Implements a TTL (Time-To-Live) caching mechanism to enhance data access performance.
"""

import time
from typing import Any, Optional
from threading import Lock


class CacheService:
    """Cache service class"""

    def __init__(self):
        """Initialize the cache service"""
        self._cache = {}
        self._timestamps = {}
        self._lock = Lock()

    def get(self, key: str, ttl: int = 900) -> Optional[Any]:
        """
        Retrieve cached data

        Args:
            key: Cache key
            ttl: Time to live (seconds), default is 15 minutes

        Returns:
            Cached value, or None if it doesn't exist or has expired
        """
        with self._lock:
            if key in self._cache:
                # Check if expired
                if time.time() - self._timestamps[key] < ttl:
                    return self._cache[key]
                else:
                    # Expired, delete cache
                    del self._cache[key]
                    del self._timestamps[key]
        return None

    def set(self, key: str, value: Any) -> None:
        """
        Set cached data

        Args:
            key: Cache key
            value: Cache value
        """
        with self._lock:
            self._cache[key] = value
            self._timestamps[key] = time.time()

    def delete(self, key: str) -> bool:
        """
        Delete cache

        Args:
            key: Cache key

        Returns:
            Whether the deletion was successful
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                del self._timestamps[key]
                return True
        return False

    def clear(self) -> None:
        """Clear all cache"""
        with self._lock:
            self._cache.clear()
            self._timestamps.clear()

    def cleanup_expired(self, ttl: int = 900) -> int:
        """
        Cleanup expired cache

        Args:
            ttl: Time to live (seconds)

        Returns:
            Number of entries cleaned
        """
        with self._lock:
            current_time = time.time()
            expired_keys = [
                key for key, timestamp in self._timestamps.items()
                if current_time - timestamp >= ttl
            ]

            for key in expired_keys:
                del self._cache[key]
                del self._timestamps[key]

            return len(expired_keys)

    def get_stats(self) -> dict:
        """
        Get cache statistics

        Returns:
            Dictionary of statistics
        """
        with self._lock:
            return {
                "total_entries": len(self._cache),
                "oldest_entry_age": (
                    time.time() - min(self._timestamps.values())
                    if self._timestamps else 0
                ),
                "newest_entry_age": (
                    time.time() - max(self._timestamps.values())
                    if self._timestamps else 0
                )
            }


# Global cache instance
_global_cache = None


def get_cache() -> CacheService:
    """
    Get global cache instance

    Returns:
        Global cache service instance
    """
    global _global_cache
    if _global_cache is None:
        _global_cache = CacheService()
    return _global_cache