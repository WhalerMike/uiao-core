"""High-performance LRU cache for UIAO-Core task processing.

Provides a thread-safe, TTL-aware LRU cache for expensive repeated operations
such as canon YAML parsing, diagram loading, and template rendering.

Usage (simple decorator)::

    from uiao_core.cache import cached, get_default_cache

    @cached(get_default_cache())
    def expensive_fn(path: str) -> dict:
        ...

Usage (async)::

    from uiao_core.cache import async_cached, get_default_cache

    @async_cached(get_default_cache())
    async def async_fn(key: str) -> dict:
        ...

Usage (standalone cache object)::

    from uiao_core.cache import UiaoLRUCache

    cache: UiaoLRUCache[str, dict] = UiaoLRUCache(maxsize=256, ttl=300)
    cache.set("key", {"data": 1})
    value = cache.get("key")
    stats = cache.stats
    cache.clear()
"""

from __future__ import annotations

import asyncio
import functools
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Callable, Generic, Hashable, TypeVar

KT = TypeVar("KT", bound=Hashable)
VT = TypeVar("VT")
F = TypeVar("F", bound=Callable[..., Any])


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------


@dataclass
class CacheStats:
    """Snapshot of cache performance metrics."""

    hits: int = field(default=0)
    misses: int = field(default=0)
    size: int = field(default=0)
    maxsize: int = field(default=128)
    ttl: float | None = field(default=None)

    @property
    def hit_rate(self) -> float:
        """Return hit rate as a fraction in [0.0, 1.0] (0.0 if no requests)."""
        total = self.hits + self.misses
        return self.hits / total if total else 0.0


# ---------------------------------------------------------------------------
# Core cache class
# ---------------------------------------------------------------------------


class UiaoLRUCache(Generic[KT, VT]):
    """Thread-safe LRU cache with optional TTL.

    Implements the LRU eviction policy on top of :class:`collections.OrderedDict`.
    When *ttl* is set, entries older than *ttl* seconds are treated as misses
    and lazily evicted on access.

    Args:
        maxsize: Maximum number of entries to retain. Must be a positive integer.
            Defaults to ``128``.
        ttl: Time-to-live in seconds. ``None`` (default) means entries never
            expire. ``0`` is treated as *no TTL*.
    """

    def __init__(self, maxsize: int = 128, ttl: float | None = None) -> None:
        if maxsize <= 0:
            raise ValueError(f"maxsize must be a positive integer, got {maxsize!r}")
        self._maxsize = maxsize
        self._ttl: float | None = ttl if (ttl and ttl > 0) else None
        self._store: OrderedDict[KT, tuple[VT, float]] = OrderedDict()
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def maxsize(self) -> int:
        """Maximum number of entries."""
        return self._maxsize

    @property
    def ttl(self) -> float | None:
        """Time-to-live in seconds, or ``None`` if entries never expire."""
        return self._ttl

    @property
    def stats(self) -> CacheStats:
        """Return a snapshot of current cache statistics."""
        with self._lock:
            return CacheStats(
                hits=self._hits,
                misses=self._misses,
                size=len(self._store),
                maxsize=self._maxsize,
                ttl=self._ttl,
            )

    def get(self, key: KT, default: VT | None = None) -> VT | None:
        """Retrieve *key* from the cache.

        Returns *default* (``None``) on a miss or when the entry has expired.
        Moves the retrieved entry to the *most-recently-used* position.
        """
        with self._lock:
            if key not in self._store:
                self._misses += 1
                return default
            value, timestamp = self._store[key]
            if self._ttl is not None and (time.monotonic() - timestamp) > self._ttl:
                # Expired — treat as miss and evict
                del self._store[key]
                self._misses += 1
                return default
            # Move to end (most-recently-used)
            self._store.move_to_end(key)
            self._hits += 1
            return value

    def set(self, key: KT, value: VT) -> None:
        """Store *value* under *key*, evicting the LRU entry if at capacity."""
        with self._lock:
            if key in self._store:
                self._store.move_to_end(key)
            self._store[key] = (value, time.monotonic())
            if len(self._store) > self._maxsize:
                self._store.popitem(last=False)  # evict LRU

    def __contains__(self, key: object) -> bool:
        """Return ``True`` if *key* is present and not expired."""
        with self._lock:
            if key not in self._store:
                return False
            _, timestamp = self._store[key]  # type: ignore[index]
            if self._ttl is not None and (time.monotonic() - timestamp) > self._ttl:
                del self._store[key]  # type: ignore[arg-type]
                return False
            return True

    def clear(self) -> None:
        """Evict all entries and reset statistics."""
        with self._lock:
            self._store.clear()
            self._hits = 0
            self._misses = 0

    def __len__(self) -> int:
        with self._lock:
            return len(self._store)

    def __repr__(self) -> str:
        s = self.stats
        return (
            f"UiaoLRUCache(maxsize={self._maxsize}, ttl={self._ttl}, "
            f"size={s.size}, hits={s.hits}, misses={s.misses})"
        )


# ---------------------------------------------------------------------------
# Decorator helpers
# ---------------------------------------------------------------------------


def cached(cache: UiaoLRUCache[Any, Any]) -> Callable[[F], F]:
    """Decorator that memoises a synchronous function using *cache*.

    The cache key is built from ``(args, frozenset(kwargs.items()))`` so all
    positional and keyword arguments are considered.  Arguments must be
    hashable.

    Example::

        my_cache: UiaoLRUCache[tuple, dict] = UiaoLRUCache(maxsize=64, ttl=60)

        @cached(my_cache)
        def load_yaml(path: str) -> dict:
            ...
    """

    def decorator(fn: F) -> F:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            key = (args, frozenset(kwargs.items()))
            result = cache.get(key)
            if result is None and key not in cache:
                result = fn(*args, **kwargs)
                cache.set(key, result)
            return result

        return wrapper  # type: ignore[return-value]

    return decorator


def async_cached(cache: UiaoLRUCache[Any, Any]) -> Callable[[F], F]:
    """Decorator that memoises an *async* function using *cache*.

    Uses an :class:`asyncio.Lock` per-call (keyed by cache instance) to
    prevent concurrent duplicate fetches for the same key (dog-pile prevention).

    Example::

        @async_cached(my_cache)
        async def fetch_data(url: str) -> dict:
            ...
    """
    # One asyncio.Lock per cache instance, created lazily
    _async_locks: dict[Any, asyncio.Lock] = {}

    def decorator(fn: F) -> F:
        @functools.wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            key = (args, frozenset(kwargs.items()))
            result = cache.get(key)
            if result is not None or key in cache:
                return result
            if key not in _async_locks:
                _async_locks[key] = asyncio.Lock()
            async with _async_locks[key]:
                # Double-check after acquiring lock
                result = cache.get(key)
                if result is not None or key in cache:
                    return result
                result = await fn(*args, **kwargs)
                cache.set(key, result)
            return result

        return wrapper  # type: ignore[return-value]

    return decorator


# ---------------------------------------------------------------------------
# Module-level default cache (configured from Settings)
# ---------------------------------------------------------------------------

_default_cache: UiaoLRUCache[Any, Any] | None = None
_default_cache_lock = threading.Lock()


def get_default_cache() -> UiaoLRUCache[Any, Any]:
    """Return (or lazily create) the module-level default cache.

    The default cache is configured from :class:`~uiao_core.config.Settings`
    (``UIAO_CACHE_SIZE`` / ``UIAO_CACHE_TTL`` env vars).
    """
    global _default_cache  # noqa: PLW0603
    if _default_cache is None:
        with _default_cache_lock:
            if _default_cache is None:
                from uiao_core.config import Settings

                try:
                    settings = Settings()
                except Exception:
                    settings = Settings(_env_file=None)  # type: ignore[call-arg]
                ttl: float | None = settings.cache_ttl if settings.cache_ttl > 0 else None
                _default_cache = UiaoLRUCache(maxsize=settings.cache_size, ttl=ttl)
    return _default_cache


def reset_default_cache() -> None:
    """Reset the module-level default cache (useful in tests)."""
    global _default_cache  # noqa: PLW0603
    with _default_cache_lock:
        _default_cache = None
