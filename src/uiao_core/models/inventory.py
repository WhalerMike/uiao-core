"""Pydantic v2 models for system inventory.

Defines the unified inventory model used by inventory loaders,
resolvers, SSP generation, and diagram generators.
"""

from __future__ import annotations

import uuid as _uuid
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ComponentType(str, Enum):
    """OSCAL-aligned component type classifications."""

    hardware = "hardware"
    software = "software"
    firmware = "firmware"
    service = "service"
    policy = "policy"
    process = "process"
    network = "network"
    other = "other"


class ItemStatus(str, Enum):
    """Operational status of an inventory item."""

    operational = "operational"
    under_development = "under-development"
    disposition = "disposition"
    other = "other"


class DataClassification(str, Enum):
    """Data classification levels."""

    unclassified = "unclassified"
    cui = "cui"
    secret = "secret"
    top_secret = "top-secret"
    public = "public"


class ConnectionDirection(str, Enum):
    """Network connection direction."""

    inbound = "inbound"
    outbound = "outbound"
    bidirectional = "bidirectional"


class InventoryItem(BaseModel):
    """A single system inventory item representing a hardware, software, or service asset."""

    uuid: str = Field(default_factory=lambda: str(_uuid.uuid4()))
    name: str
    type: ComponentType = ComponentType.software
    vendor: str = ""
    version: str = ""
    ip_address: str = ""
    fqdn: str = ""
    location: str = ""
    status: ItemStatus = ItemStatus.operational
    description: str = ""
    source: str = ""
    source_id: str = ""
    implemented_components: list[str] = Field(default_factory=list)
    props: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="allow")


class Connection(BaseModel):
    """A directed network or data connection between two inventory items."""

    source: str
    destination: str
    protocol: str = ""
    port: int | None = None
    direction: ConnectionDirection = ConnectionDirection.bidirectional
    data_classification: DataClassification = DataClassification.unclassified
    description: str = ""

    model_config = ConfigDict(extra="allow")


class DataFlow(BaseModel):
    """A data flow describing data movement from a source through processing to storage."""

    name: str
    source: str
    processor: str = ""
    destination: str
    data_classification: DataClassification = DataClassification.unclassified
    description: str = ""

    model_config = ConfigDict(extra="allow")


class SystemInventory(BaseModel):
    """The unified system inventory aggregated from all configured sources."""

    items: list[InventoryItem] = Field(default_factory=list)
    connections: list[Connection] = Field(default_factory=list)
    data_flows: list[DataFlow] = Field(default_factory=list)

    model_config = ConfigDict(extra="allow")

    def get_by_type(self, component_type: ComponentType) -> list[InventoryItem]:
        """Return all items of a given component type."""
        return [i for i in self.items if i.type == component_type]

    def get_by_name(self, name: str) -> InventoryItem | None:
        """Return first item matching the given name (case-insensitive)."""
        name_lower = name.lower()
        for item in self.items:
            if item.name.lower() == name_lower:
                return item
        return None

    def summary(self) -> dict[str, int]:
        """Return a count-by-type summary of inventory items."""
        counts: dict[str, int] = {}
        for item in self.items:
            counts[item.type.value] = counts.get(item.type.value, 0) + 1
        return counts
