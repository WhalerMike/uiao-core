"""Inventory package for uiao_core.

Provides multi-source inventory loading, normalization, and diagram generation.
"""

from __future__ import annotations

from .loader import InventoryLoader
from .resolver import InventoryResolver

__all__ = ["InventoryLoader", "InventoryResolver"]
