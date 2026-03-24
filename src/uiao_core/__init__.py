"""UIAO Core - Unified Identity-Addressing-Overlay Architecture.

FedRAMP modernization pipeline package providing type-safe YAML loading,
OSCAL generation, and CLI tooling for federal cloud compliance.
"""

from .__version__ import __version__
from .cache import CacheStats, UiaoLRUCache, async_cached, cached, get_default_cache

__all__ = [
    "__version__",
    "UiaoLRUCache",
    "CacheStats",
    "cached",
    "async_cached",
    "get_default_cache",
]
