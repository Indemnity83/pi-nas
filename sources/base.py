"""Base class for cached data sources."""

import time
from typing import Any, Optional


class CachedDataSource:
    """Base class for data sources with TTL-based caching."""

    def __init__(self):
        self._cache = {}
        self._timestamps = {}

    def get(self, key: str, ttl_s: float = 10.0) -> Any:
        """
        Get data by key with TTL-based caching.

        Args:
            key: Data key to fetch
            ttl_s: Time-to-live in seconds (default: 10.0)

        Returns:
            Cached or freshly fetched data
        """
        now = time.time()

        # Check cache
        if key in self._cache:
            if now - self._timestamps[key] < ttl_s:
                return self._cache[key]

        # Fetch fresh data
        value = self._fetch(key)

        # Update cache
        self._cache[key] = value
        self._timestamps[key] = now

        return value

    def invalidate(self, key: Optional[str] = None):
        """
        Invalidate cache for a specific key or all keys.

        Args:
            key: Specific key to invalidate, or None for all
        """
        if key is None:
            self._cache.clear()
            self._timestamps.clear()
        else:
            self._cache.pop(key, None)
            self._timestamps.pop(key, None)

    def _fetch(self, key: str) -> Any:
        """
        Fetch data for the given key.

        Must be implemented by subclasses.

        Args:
            key: Data key to fetch

        Returns:
            Fetched data
        """
        raise NotImplementedError("Subclasses must implement _fetch()")
