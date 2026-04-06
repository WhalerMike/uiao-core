"""
UIAO-Core Canonical BaseAdapter ABC

Reconciles the two competing base classes that existed in the repo:
  - adapters/base_adapter.py  (compliance-plane ABC: extract_claims, lineage, KSI)
  - src/uiao_core/adapters/database_base.py  (operational ABC: connect, schema, query, normalize)

This single ABC is the new SSOT.  Both original files become thin shims that
re-export from here so existing imports continue to work without change.

Canonical location: src/uiao_core/adapters/base_adapter.py
"""
from __future__ import annotations

import abc
import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Adapter taxonomy
# ---------------------------------------------------------------------------

class AdapterType(str, Enum):
    """
    Four canonical planes from the UIAO adapter framework.
    Every concrete adapter declares which plane it belongs to via ADAPTER_TYPE.
    """
    IDENTITY     = "Identity"      # Entra ID, Okta, Active Directory ...
    NETWORK      = "Network"       # Zscaler, Cisco ISE, Palo Alto ...
    DATA_API     = "DataAPI"       # ServiceNow, Jira, Splunk ...
    CLOUD_INFRA  = "CloudInfra"    # AWS, Azure ARM, GCP ...


# ---------------------------------------------------------------------------
# Provenance & canonical dataclasses (merged from both ABCs)
# ---------------------------------------------------------------------------

@dataclass
class AdapterMetadata:
    adapter_id:         str
    name:               str
    version:            str
    adapter_type:       AdapterType
    certification_level: int          = 1
    capabilities:       List[str]     = field(default_factory=list)


@dataclass
class ConnectionProvenance:
    identity:    str
    auth_method: str
    endpoint:    str
    tls_version: Optional[str]
    mtls_enabled: bool
    timestamp:   datetime

    def to_dict(self):
        return {
            "identity":     self.identity,
            "auth_method":  self.auth_method,
            "endpoint":     self.endpoint,
            "tls_version":  self.tls_version,
            "mtls_enabled": self.mtls_enabled,
            "timestamp":    self.timestamp.isoformat(),
        }


@dataclass
class SchemaMappingObject:
    vendor_schema:    Dict[str, Any]
    canonical_schema: Dict[str, Any]
    mapping_rules:    Dict[str, Any]
    unmapped_fields:  List[str]
    version_hash:     str

    def to_dict(self):
        return {
            "vendor_schema":    self.vendor_schema,
            "canonical_schema": self.canonical_schema,
            "mapping_rules":    self.mapping_rules,
            "unmapped_fields":  self.unmapped_fields,
            "version_hash":     self.version_hash,
        }


@dataclass
class QueryProvenance:
    canonical_query:      Dict[str, Any]
    vendor_query:         str
    execution_plan_hash:  str
    row_count:            int
    timestamp:            datetime

    def to_dict(self):
        return {
            "canonical_query":     self.canonical_query,
            "vendor_query":        self.vendor_query,
            "execution_plan_hash": self.execution_plan_hash,
            "row_count":           self.row_count,
            "timestamp":           self.timestamp.isoformat(),
        }


@dataclass
class ClaimObject:
    claim_id:       str
    entity:         str
    fields:         Dict[str, Any]
    source:         str
    provenance_hash: str

    def to_dict(self):
        return {
            "claim_id":        self.claim_id,
            "entity":          self.entity,
            "fields":          self.fields,
            "source":          self.source,
            "provenance_hash": self.provenance_hash,
        }


@dataclass
class ClaimSet:
    claims:           List[ClaimObject]
    source_reference: str

    def to_dict(self):
        return {
            "claims":           [c.to_dict() for c in self.claims],
            "source_reference": self.source_reference,
        }


@dataclass
class ClaimFilter:
    source_system: str = ""
    claim_type:    str = ""


@dataclass
class DriftReport:
    drift_type:      str
    severity:        str
    first_observed:  datetime
    last_observed:   datetime
    details:         Dict[str, Any]
    remediation:     Optional[str] = None

    def to_dict(self):
        return {
            "drift_type":     self.drift_type,
            "severity":       self.severity,
            "first_observed": self.first_observed.isoformat(),
            "last_observed":  self.last_observed.isoformat(),
            "details":        self.details,
            "remediation":    self.remediation,
        }


@dataclass
class ProvenanceRecord:
    record_id:     str
    adapter_id:    str
    source_system: str = ""

    def to_dict(self):
        return {
            "record_id":     self.record_id,
            "adapter_id":    self.adapter_id,
            "source_system": self.source_system,
        }


@dataclass
class KSIBundle:
    bundle_id:  str
    adapter_id: str

    def to_dict(self):
        return {"bundle_id": self.bundle_id, "adapter_id": self.adapter_id}


@dataclass
class EvidenceObject:
    ksi_id:          str
    source:          str
    timestamp:       datetime
    raw_data:        Any
    normalized_data: Optional[Dict[str, Any]]
    provenance:      Dict[str, Any]
    freshness_valid: bool = False

    def to_dict(self):
        return {
            "ksi_id":          self.ksi_id,
            "source":          self.source,
            "timestamp":       self.timestamp.isoformat(),
            "raw_data":        self.raw_data,
            "normalized_data": self.normalized_data,
            "provenance":      self.provenance,
            "freshness_valid": self.freshness_valid,
        }


# ---------------------------------------------------------------------------
# Canonical BaseAdapter ABC
# ---------------------------------------------------------------------------

class BaseAdapter(abc.ABC):
    """
    Canonical Abstract Base Class for all UIAO adapters.

    Every adapter MUST:
      - declare ADAPTER_ID  (unique slug, e.g. "entra", "servicenow")
      - declare ADAPTER_TYPE (one of AdapterType enum values)
      - implement all @abstractmethod methods below

    Responsibility domains (from adapter-framework.qmd):
      2.1  Connection & Identity
      2.2  Schema Discovery & Canonical Mapping
      2.3  Query Normalization & Deterministic Extraction
      2.4  Data Normalization & Claim Construction
      2.5  Drift Detection & Version Integrity
      2.6  Evidence Packaging & KSI Integration
      2.7  Security, Privacy, and Operational Controls

    Compliance-plane methods (from adapters/base_adapter.py heritage):
      extract_claims, transform_to_canonical, generate_lineage,
      generate_ksi_bundle, get_metadata
    """

    ADAPTER_ID:   str         = "base"
    ADAPTER_TYPE: AdapterType = AdapterType.DATA_API

    def __init__(self, config=None):
        self._config = config or {}

    # ------------------------------------------------------------------
    # Helper utilities
    # ------------------------------------------------------------------

    def _now(self):
        return datetime.now(timezone.utc)

    def _hash(self, payload):
        try:
            serialized = json.dumps(payload, sort_keys=True, default=str)
        except Exception:
            serialized = str(payload)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    # ------------------------------------------------------------------
    # 2.1  Connection & Identity
    # ------------------------------------------------------------------

    @abc.abstractmethod
    def connect(self) -> ConnectionProvenance:
        """Establish a secure, authenticated connection; return provenance."""
        raise NotImplementedError

    # ------------------------------------------------------------------
    # 2.2  Schema Discovery & Canonical Mapping
    # ------------------------------------------------------------------

    @abc.abstractmethod
    def discover_schema(self) -> SchemaMappingObject:
        """Discover vendor schema and map to UIAO canonical schema."""
        raise NotImplementedError

    # ------------------------------------------------------------------
    # 2.3  Query Normalization & Deterministic Extraction
    # ------------------------------------------------------------------

    @abc.abstractmethod
    def execute_query(self, canonical_query) -> QueryProvenance:
        """Translate canonical query to vendor query and execute deterministically."""
        raise NotImplementedError

    # ------------------------------------------------------------------
    # 2.4  Data Normalization & Claim Construction
    # ------------------------------------------------------------------

    @abc.abstractmethod
    def normalize(self, raw_rows) -> ClaimSet:
        """Convert raw vendor records into canonical ClaimObjects."""
        raise NotImplementedError

    @abc.abstractmethod
    def extract_claims(self, filter) -> List[ClaimObject]:
        """Return filtered canonical claims (compliance-plane view)."""
        raise NotImplementedError

    @abc.abstractmethod
    def transform_to_canonical(self, raw) -> ClaimObject:
        """Transform a single raw vendor record into a canonical ClaimObject."""
        raise NotImplementedError

    # ------------------------------------------------------------------
    # 2.5  Drift Detection & Version Integrity
    # ------------------------------------------------------------------

    @abc.abstractmethod
    def detect_drift(self) -> DriftReport:
        """Detect schema, constraint, cardinality, or semantic drift."""
        raise NotImplementedError

    # ------------------------------------------------------------------
    # 2.6  Evidence Packaging & KSI Integration
    # ------------------------------------------------------------------

    @abc.abstractmethod
    def generate_lineage(self) -> ProvenanceRecord:
        """Produce a provenance record for the full adapter run."""
        raise NotImplementedError

    @abc.abstractmethod
    def generate_ksi_bundle(self) -> KSIBundle:
        """Produce a KSI evidence bundle for submission to the registry."""
        raise NotImplementedError

    def collect_evidence(self, ksi_id: str) -> EvidenceObject:
        """
        Default orchestration of all domains into one EvidenceObject.
        detect_drift() MUST be called before any claim is emitted (canon rule).
        """
        conn_prov  = self.connect()
        schema_map = self.discover_schema()
        canonical_query = {"select": ["*"], "from": "canonical_entity"}
        query_prov = self.execute_query(canonical_query)
        raw_rows   = []
        claim_set  = self.normalize(raw_rows)
        drift      = self.detect_drift()   # MUST run before emit

        return EvidenceObject(
            ksi_id=ksi_id,
            source=self.ADAPTER_ID,
            timestamp=self._now(),
            raw_data={
                "connection":     conn_prov.to_dict(),
                "schema_mapping": schema_map.to_dict(),
                "query":          query_prov.to_dict(),
                "drift":          drift.to_dict(),
            },
            normalized_data=claim_set.to_dict(),
            provenance={
                "adapter_id": self.ADAPTER_ID,
                "hash":       self._hash(claim_set.to_dict()),
                "timestamp":  self._now().isoformat(),
            },
            freshness_valid=False,
        )

    # ------------------------------------------------------------------
    # 2.7  Metadata
    # ------------------------------------------------------------------

    @abc.abstractmethod
    def get_metadata(self) -> AdapterMetadata:
        """Return the adapter's self-description for the FIMF registry."""
        raise NotImplementedError
