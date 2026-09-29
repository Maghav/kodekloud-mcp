"""Tests for in-memory TTL cache functionality."""

import asyncio

import pytest

from kodekloud_mcp.cache import TTLCache


@pytest.mark.asyncio
async def test_cache_hit_and_miss() -> None:
    """Verify cache stores and retrieves unexpired values."""
    cache = TTLCache(default_ttl_seconds=60)
    assert await cache.get("nonexistent") is None

    await cache.set("my_key", {"data": 123})
    cached = await cache.get("my_key")
    assert cached == {"data": 123}


@pytest.mark.asyncio
async def test_cache_expiration() -> None:
    """Verify values expire after their TTL duration."""
    cache = TTLCache(default_ttl_seconds=1)
    await cache.set("short_key", "hello", ttl_seconds=1)

    # Immediate retrieval succeeds
    assert await cache.get("short_key") == "hello"

    # Sleep past expiration
    await asyncio.sleep(1.1)
    assert await cache.get("short_key") is None


@pytest.mark.asyncio
async def test_cache_invalidation() -> None:
    """Verify invalidating a key removes it from cache."""
    cache = TTLCache(default_ttl_seconds=60)
    await cache.set("key1", "val1")
    await cache.set("key2", "val2")

    await cache.invalidate("key1")
    assert await cache.get("key1") is None
    assert await cache.get("key2") == "val2"


@pytest.mark.asyncio
async def test_cache_clear() -> None:
    """Verify clearing cache purges all entries."""
    cache = TTLCache(default_ttl_seconds=60)
    await cache.set("key1", "val1")
    await cache.set("key2", "val2")

    await cache.clear()
    assert await cache.get("key1") is None
    assert await cache.get("key2") is None


def test_make_key() -> None:
    """Verify deterministic cache key generation."""
    key1 = TTLCache.make_key("user_progress", course_id="cka", page=1)
    key2 = TTLCache.make_key("user_progress", page=1, course_id="cka")
    assert key1 == key2
    assert key1 == "user_progress:course_id=cka&page=1"
