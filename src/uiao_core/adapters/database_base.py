"""
database_base.py -- backwards-compatibility shim

This file intentionally contains no logic.  It re-exports every public name
from the canonical BaseAdapter module so that all existing code that does:

    from .database_base import DatabaseAdapterBase
    from .database_base import ClaimObject, ClaimSet, DriftReport, ...

continues to work without any changes.

The real implementation lives in:
    src/uiao_core/adapters/base_adapter.py
"""
from .base_adapter import (  # noqa: F401  -- re-export everything
    AdapterType,
    AdapterMetadata,
    ConnectionProvenance,
    SchemaMappingObject,
    QueryProvenance,
    ClaimObject,
    ClaimSet,
    ClaimFilter,
    DriftReport,
    ProvenanceRecord,
    KSIBundle,
    EvidenceObject,
    BaseAdapter as DatabaseAdapterBase,   # legacy alias
)

# Keep the old name available directly
DatabaseAdapterBase = DatabaseAdapterBase  # noqa: F811

__all__ = [
    "AdapterType",
    "AdapterMetadata",
    "ConnectionProvenance",
    "SchemaMappingObject",
    "QueryProvenance",
    "ClaimObject",
    "ClaimSet",
    "ClaimFilter",
    "DriftReport",
    "ProvenanceRecord",
    "KSIBundle",
    "EvidenceObject",
    "DatabaseAdapterBase",
]
