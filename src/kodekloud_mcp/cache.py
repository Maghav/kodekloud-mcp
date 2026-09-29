"""In-memory TTL cache for kodekloud-mcp.

Stores recent API responses in memory for a configurable duration (default 60 seconds)
to prevent redundant queries and avoid hammering KodeKloud servers.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any


class TTLCache:
    """A thread-safe and asyncio-safe in-memory cache with time-to-live expiration."""

    def __init__(self, default_ttl_seconds: int = 60) -> None:
        self.default_ttl = default_ttl_seconds
        # Storage: key -> (value, expiry_timestamp)
        self._cache: dict[str, tuple[Any, float]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Any | None:
        """Retrieve a cached value if present and unexpired."""
        async with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None
            value, expiry = entry
            if time.time() > expiry:
                # Expired
                del self._cache[key]
                return None
            return value

    async def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        """Store a value with an expiration timestamp."""
        ttl = self.default_ttl if ttl_seconds is None else ttl_seconds
        expiry = time.time() + ttl
        async with self._lock:
            self._cache[key] = (value, expiry)

    async def invalidate(self, key: str) -> None:
        """Remove a specific key from the cache."""
        async with self._lock:
            self._cache.pop(key, None)

    async def clear(self) -> None:
        """Clear all entries from the cache."""
        async with self._lock:
            self._cache.clear()

    @staticmethod
    def make_key(namespace: str, **kwargs: Any) -> str:
        """Create a deterministic cache key from namespace and keyword arguments."""
        sorted_items = sorted((k, str(v)) for k, v in kwargs.items())
        params_str = "&".join(f"{k}={v}" for k, v in sorted_items)
        return f"{namespace}:{params_str}" if params_str else namespace
