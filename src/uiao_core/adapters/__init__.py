"""
UIAO-Core Adapters Package.

All adapter classes and types are exported here for convenient import.
Adapters are DNS-style alignment resolvers -- they do NOT perform heavy
OSCAL/SBOM/SSP conversions.  That work lives in generators/.

Public surface:
  BaseAdapter      -- canonical ABC (new SSOT)
  AdapterType      -- four-plane taxonomy enum
  DatabaseAdapterBase -- legacy alias for BaseAdapter (BC shim)
  EntraAdapter     -- Microsoft Entra ID adapter
  ServiceNowAdapter -- ServiceNow adapter
"""
from .base_adapter import (  # noqa: F401
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
    BaseAdapter,
)
from .database_base import DatabaseAdapterBase  # noqa: F401  BC shim re-export
from .entra_adapter import EntraAdapter          # noqa: F401
from .servicenow_adapter import ServiceNowAdapter  # noqa: F401

__all__ = [
    # Canonical
    "BaseAdapter",
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
    # Legacy alias (BC)
    "DatabaseAdapterBase",
    # Concrete adapters
    "EntraAdapter",
    "ServiceNowAdapter",
]
