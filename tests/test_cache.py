"""Tests for uiao_core.cache module."""

from __future__ import annotations

import asyncio
import time
from typing import Any

import pytest

from uiao_core.cache import (
    CacheStats,
    UiaoLRUCache,
    async_cached,
    cached,
    get_default_cache,
    reset_default_cache,
)


# ---------------------------------------------------------------------------
# UiaoLRUCache – basic operations
# ---------------------------------------------------------------------------


class TestUiaoLRUCacheBasic:
    """Basic get/set/contains behaviour."""

    def test_set_and_get(self) -> None:
        cache: UiaoLRUCache[str, int] = UiaoLRUCache(maxsize=4)
        cache.set("a", 1)
        assert cache.get("a") == 1

    def test_get_missing_returns_default(self) -> None:
        cache: UiaoLRUCache[str, int] = UiaoLRUCache(maxsize=4)
        assert cache.get("missing") is None
        assert cache.get("missing", 42) == 42  # type: ignore[arg-type]

    def test_contains_present(self) -> None:
        cache: UiaoLRUCache[str, int] = UiaoLRUCache(maxsize=4)
        cache.set("x", 99)
        assert "x" in cache

    def test_contains_absent(self) -> None:
        cache: UiaoLRUCache[str, int] = UiaoLRUCache(maxsize=4)
        assert "nope" not in cache

    def test_len(self) -> None:
        cache: UiaoLRUCache[str, int] = UiaoLRUCache(maxsize=4)
        assert len(cache) == 0
        cache.set("a", 1)
        cache.set("b", 2)
        assert len(cache) == 2

    def test_overwrite_existing_key(self) -> None:
        cache: UiaoLRUCache[str, int] = UiaoLRUCache(maxsize=4)
        cache.set("k", 1)
        cache.set("k", 2)
        assert cache.get("k") == 2
        assert len(cache) == 1

    def test_clear_resets_entries_and_stats(self) -> None:
        cache: UiaoLRUCache[str, int] = UiaoLRUCache(maxsize=4)
        cache.set("a", 1)
        cache.get("a")
        cache.get("missing")
        cache.clear()
        assert len(cache) == 0
        stats = cache.stats
        assert stats.hits == 0
        assert stats.misses == 0

    def test_invalid_maxsize_raises(self) -> None:
        with pytest.raises(ValueError):
            UiaoLRUCache(maxsize=0)
        with pytest.raises(ValueError):
            UiaoLRUCache(maxsize=-1)

    def test_repr_contains_key_info(self) -> None:
        cache: UiaoLRUCache[str, int] = UiaoLRUCache(maxsize=8)
        r = repr(cache)
        assert "maxsize=8" in r


# ---------------------------------------------------------------------------
# LRU eviction
# ---------------------------------------------------------------------------


class TestLRUEviction:
    """Verify LRU eviction order."""

    def test_evicts_lru_entry_when_full(self) -> None:
        cache: UiaoLRUCache[str, int] = UiaoLRUCache(maxsize=3)
        for i, k in enumerate(["a", "b", "c"]):
            cache.set(k, i)
        # Access "a" to make it recently used; "b" becomes LRU
        cache.get("a")
        # Insert "d" — "b" should be evicted
        cache.set("d", 99)
        assert "b" not in cache
        assert "a" in cache
        assert "c" in cache
        assert "d" in cache

    def test_maxsize_maintained(self) -> None:
        cache: UiaoLRUCache[int, int] = UiaoLRUCache(maxsize=5)
        for i in range(20):
            cache.set(i, i)
        assert len(cache) == 5


# ---------------------------------------------------------------------------
# TTL support
# ---------------------------------------------------------------------------


class TestTTL:
    """TTL expiry behaviour."""

    def test_entry_valid_before_ttl(self) -> None:
        cache: UiaoLRUCache[str, str] = UiaoLRUCache(maxsize=4, ttl=60)
        cache.set("k", "v")
        assert cache.get("k") == "v"
        assert "k" in cache

    def test_entry_expired_after_ttl(self) -> None:
        cache: UiaoLRUCache[str, str] = UiaoLRUCache(maxsize=4, ttl=0.05)
        cache.set("k", "v")
        time.sleep(0.1)
        assert cache.get("k") is None
        assert "k" not in cache

    def test_zero_ttl_treated_as_no_expiry(self) -> None:
        cache: UiaoLRUCache[str, str] = UiaoLRUCache(maxsize=4, ttl=0)
        assert cache.ttl is None
        cache.set("k", "v")
        assert cache.get("k") == "v"

    def test_none_ttl_treated_as_no_expiry(self) -> None:
        cache: UiaoLRUCache[str, str] = UiaoLRUCache(maxsize=4, ttl=None)
        assert cache.ttl is None


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------


class TestCacheStats:
    """CacheStats dataclass and hit-rate calculation."""

    def test_stats_tracks_hits_and_misses(self) -> None:
        cache: UiaoLRUCache[str, int] = UiaoLRUCache(maxsize=4)
        cache.set("a", 1)
        cache.get("a")  # hit
        cache.get("a")  # hit
        cache.get("b")  # miss
        stats = cache.stats
        assert stats.hits == 2
        assert stats.misses == 1
        assert stats.size == 1

    def test_hit_rate_zero_on_empty(self) -> None:
        stats = CacheStats()
        assert stats.hit_rate == 0.0

    def test_hit_rate_calculation(self) -> None:
        stats = CacheStats(hits=3, misses=1)
        assert stats.hit_rate == pytest.approx(0.75)

    def test_stats_maxsize_and_ttl(self) -> None:
        cache: UiaoLRUCache[str, int] = UiaoLRUCache(maxsize=32, ttl=120)
        stats = cache.stats
        assert stats.maxsize == 32
        assert stats.ttl == 120


# ---------------------------------------------------------------------------
# Thread safety (smoke test)
# ---------------------------------------------------------------------------


class TestThreadSafety:
    """Ensure concurrent reads/writes don't corrupt state."""

    def test_concurrent_sets(self) -> None:
        import threading

        cache: UiaoLRUCache[int, int] = UiaoLRUCache(maxsize=100)
        errors: list[Exception] = []

        def writer(start: int) -> None:
            try:
                for i in range(start, start + 50):
                    cache.set(i, i * 2)
            except Exception as exc:  # noqa: BLE001
                errors.append(exc)

        threads = [threading.Thread(target=writer, args=(i * 50,)) for i in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors
        assert len(cache) <= 100


# ---------------------------------------------------------------------------
# @cached decorator
# ---------------------------------------------------------------------------


class TestCachedDecorator:
    """Synchronous @cached decorator."""

    def test_caches_return_value(self) -> None:
        call_count = 0
        cache: UiaoLRUCache[Any, int] = UiaoLRUCache(maxsize=8)

        @cached(cache)
        def add(a: int, b: int) -> int:
            nonlocal call_count
            call_count += 1
            return a + b

        assert add(1, 2) == 3
        assert add(1, 2) == 3
        assert call_count == 1  # second call served from cache

    def test_different_args_cache_separately(self) -> None:
        cache: UiaoLRUCache[Any, int] = UiaoLRUCache(maxsize=8)

        @cached(cache)
        def square(n: int) -> int:
            return n * n

        assert square(3) == 9
        assert square(4) == 16
        assert len(cache) == 2

    def test_kwargs_are_part_of_cache_key(self) -> None:
        cache: UiaoLRUCache[Any, str] = UiaoLRUCache(maxsize=8)
        calls: list[tuple[Any, ...]] = []

        @cached(cache)
        def greet(name: str, greeting: str = "hello") -> str:
            calls.append((name, greeting))
            return f"{greeting} {name}"

        greet("alice")
        greet("alice", greeting="hi")
        assert len(calls) == 2  # different kwargs → different cache entries


# ---------------------------------------------------------------------------
# @async_cached decorator
# ---------------------------------------------------------------------------


class TestAsyncCachedDecorator:
    """Async @async_cached decorator."""

    def test_async_caches_return_value(self) -> None:
        call_count = 0
        cache: UiaoLRUCache[Any, int] = UiaoLRUCache(maxsize=8)

        @async_cached(cache)
        async def fetch(n: int) -> int:
            nonlocal call_count
            call_count += 1
            return n * 10

        async def run() -> None:
            nonlocal call_count
            result1 = await fetch(5)
            result2 = await fetch(5)
            assert result1 == 50
            assert result2 == 50
            assert call_count == 1

        asyncio.run(run())

    def test_async_different_args_cache_separately(self) -> None:
        cache: UiaoLRUCache[Any, int] = UiaoLRUCache(maxsize=8)

        @async_cached(cache)
        async def double(n: int) -> int:
            return n * 2

        async def run() -> None:
            assert await double(3) == 6
            assert await double(7) == 14
            assert len(cache) == 2

        asyncio.run(run())


# ---------------------------------------------------------------------------
# Default cache / reset
# ---------------------------------------------------------------------------


class TestDefaultCache:
    """Module-level default cache singleton."""

    def setup_method(self) -> None:
        reset_default_cache()

    def teardown_method(self) -> None:
        reset_default_cache()

    def test_get_default_cache_returns_instance(self) -> None:
        c = get_default_cache()
        assert isinstance(c, UiaoLRUCache)

    def test_get_default_cache_is_singleton(self) -> None:
        c1 = get_default_cache()
        c2 = get_default_cache()
        assert c1 is c2

    def test_reset_clears_singleton(self) -> None:
        c1 = get_default_cache()
        reset_default_cache()
        c2 = get_default_cache()
        assert c1 is not c2
