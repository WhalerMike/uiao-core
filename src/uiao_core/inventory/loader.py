"""Inventory data loader supporting multiple source types.

Supported sources:
- YAML: core-stack.yml or any inventory YAML
- Terraform state JSON (terraform.tfstate)
- Azure Resource Graph query results (JSON)
- AWS Config snapshot (JSON)
- Generic CSV inventory
- Generic JSON inventory
"""

from __future__ import annotations

import csv
import json
import logging
from io import StringIO
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


class InventoryLoader:
    """Loads raw inventory records from multiple source types.

    Each load method returns a list of raw dicts with a ``_source`` key
    indicating which loader produced the record. The resolver normalizes
    these into :class:`~uiao_core.models.inventory.InventoryItem` objects.
    """

    # ------------------------------------------------------------------ #
    # YAML sources
    # ------------------------------------------------------------------ #

    @staticmethod
    def load_yaml(path: str | Path) -> list[dict[str, Any]]:
        """Load inventory items from a YAML file.

        Supports two layouts:
        - A top-level list of component dicts (core-stack.yml style)
        - A top-level dict with an ``inventory_items`` or ``components`` key
        """
        p = Path(path)
        if not p.exists():
            logger.warning("YAML source not found: %s", p)
            return []

        with p.open(encoding="utf-8") as fh:
            data = yaml.safe_load(fh)

        records: list[dict[str, Any]] = []

        if isinstance(data, list):
            records = [dict(r) for r in data if isinstance(r, dict)]
        elif isinstance(data, dict):
            # Try common wrapper keys
            for key in ("inventory_items", "components", "items", "resources"):
                if isinstance(data.get(key), list):
                    records = [dict(r) for r in data[key] if isinstance(r, dict)]
                    break
            if not records:
                # Treat the whole dict as a single record
                records = [dict(data)]

        for rec in records:
            rec.setdefault("_source", "yaml")
            rec.setdefault("_source_file", str(p))
        return records

    # ------------------------------------------------------------------ #
    # Terraform state
    # ------------------------------------------------------------------ #

    @staticmethod
    def load_terraform_state(path: str | Path) -> list[dict[str, Any]]:
        """Parse a terraform.tfstate JSON file and extract managed resources."""
        p = Path(path)
        if not p.exists():
            logger.warning("Terraform state not found: %s", p)
            return []

        with p.open(encoding="utf-8") as fh:
            state: dict[str, Any] = json.load(fh)

        records: list[dict[str, Any]] = []
        resources: list[dict[str, Any]] = state.get("resources", [])

        for resource in resources:
            if not isinstance(resource, dict):
                continue
            rtype = resource.get("type", "")
            rname = resource.get("name", "")
            mode = resource.get("mode", "managed")
            if mode != "managed":
                continue

            for instance in resource.get("instances", [{}]):
                attrs = instance.get("attributes", {}) if isinstance(instance, dict) else {}
                records.append({
                    "_source": "terraform",
                    "_source_file": str(p),
                    "id": attrs.get("id", f"{rtype}.{rname}"),
                    "name": attrs.get("name") or rname,
                    "type": rtype,
                    "location": attrs.get("location", ""),
                    "resource_group": attrs.get("resource_group_name", ""),
                    "tags": attrs.get("tags") or {},
                    "attrs": attrs,
                })

        return records

    # ------------------------------------------------------------------ #
    # Azure Resource Graph
    # ------------------------------------------------------------------ #

    @staticmethod
    def load_azure_resource_graph(path: str | Path) -> list[dict[str, Any]]:
        """Load Azure Resource Graph query results from a JSON file.

        Expected format: ``{"data": [...]}`` or a bare list of resource objects.
        """
        p = Path(path)
        if not p.exists():
            logger.warning("Azure Resource Graph JSON not found: %s", p)
            return []

        with p.open(encoding="utf-8") as fh:
            payload: Any = json.load(fh)

        raw: list[Any] = []
        if isinstance(payload, list):
            raw = payload
        elif isinstance(payload, dict):
            raw = payload.get("data", payload.get("value", []))

        records: list[dict[str, Any]] = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            records.append({
                "_source": "azure",
                "_source_file": str(p),
                "id": item.get("id", ""),
                "name": item.get("name", ""),
                "type": item.get("type", ""),
                "location": item.get("location", ""),
                "resource_group": item.get("resourceGroup", ""),
                "sku": item.get("sku", {}).get("name", "") if isinstance(item.get("sku"), dict) else "",
                "tags": item.get("tags") or {},
                "attrs": item,
            })
        return records

    # ------------------------------------------------------------------ #
    # AWS Config snapshot
    # ------------------------------------------------------------------ #

    @staticmethod
    def load_aws_config(path: str | Path) -> list[dict[str, Any]]:
        """Load AWS Config configuration snapshot JSON.

        Expected format: ``{"configurationItems": [...]}``
        """
        p = Path(path)
        if not p.exists():
            logger.warning("AWS Config snapshot not found: %s", p)
            return []

        with p.open(encoding="utf-8") as fh:
            payload: Any = json.load(fh)

        raw: list[Any] = []
        if isinstance(payload, list):
            raw = payload
        elif isinstance(payload, dict):
            raw = payload.get("configurationItems", payload.get("items", []))

        records: list[dict[str, Any]] = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            records.append({
                "_source": "aws",
                "_source_file": str(p),
                "id": item.get("resourceId", ""),
                "name": item.get("resourceName", item.get("resourceId", "")),
                "type": item.get("resourceType", ""),
                "region": item.get("awsRegion", ""),
                "account": item.get("accountId", ""),
                "arn": item.get("arn", ""),
                "tags": item.get("tags") or {},
                "attrs": item,
            })
        return records

    # ------------------------------------------------------------------ #
    # CSV
    # ------------------------------------------------------------------ #

    @staticmethod
    def load_csv(path: str | Path) -> list[dict[str, Any]]:
        """Load a generic CSV inventory file.

        Any column headers become dict keys. A ``name`` column is required;
        other columns are treated as attributes.
        """
        p = Path(path)
        if not p.exists():
            logger.warning("CSV inventory not found: %s", p)
            return []

        records: list[dict[str, Any]] = []
        with p.open(encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                rec = dict(row)
                rec["_source"] = "csv"
                rec["_source_file"] = str(p)
                records.append(rec)
        return records

    # ------------------------------------------------------------------ #
    # Generic JSON
    # ------------------------------------------------------------------ #

    @staticmethod
    def load_json(path: str | Path) -> list[dict[str, Any]]:
        """Load a generic JSON inventory file.

        Accepts either a list of item dicts or a dict with an ``items`` /
        ``data`` / ``resources`` key containing a list.
        """
        p = Path(path)
        if not p.exists():
            logger.warning("JSON inventory not found: %s", p)
            return []

        with p.open(encoding="utf-8") as fh:
            payload: Any = json.load(fh)

        raw: list[Any] = []
        if isinstance(payload, list):
            raw = payload
        elif isinstance(payload, dict):
            for key in ("items", "data", "resources", "inventory"):
                if isinstance(payload.get(key), list):
                    raw = payload[key]
                    break
            if not raw:
                raw = [payload]

        records: list[dict[str, Any]] = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            rec = dict(item)
            rec.setdefault("_source", "json")
            rec.setdefault("_source_file", str(p))
            records.append(rec)
        return records

    # ------------------------------------------------------------------ #
    # Config-driven loader
    # ------------------------------------------------------------------ #

    @classmethod
    def load_from_config(cls, config: dict[str, Any]) -> list[dict[str, Any]]:
        """Load all inventory sources defined in ``inventory_sources.yaml``.

        ``config`` should be the parsed content of the config file, which
        must contain a top-level ``sources`` list.  Each source entry has:

        .. code-block:: yaml

           sources:
             - type: yaml          # yaml | terraform | azure | aws | csv | json
               path: data/core-stack.yml
               enabled: true       # optional, defaults to true
        """
        sources = config.get("sources", [])
        if not isinstance(sources, list):
            return []

        all_records: list[dict[str, Any]] = []
        for source in sources:
            if not isinstance(source, dict):
                continue
            if not source.get("enabled", True):
                continue
            src_type = source.get("type", "").lower()
            src_path = source.get("path", "")
            if not src_path:
                logger.warning("Inventory source missing 'path': %s", source)
                continue

            loader_map = {
                "yaml": cls.load_yaml,
                "terraform": cls.load_terraform_state,
                "azure": cls.load_azure_resource_graph,
                "aws": cls.load_aws_config,
                "csv": cls.load_csv,
                "json": cls.load_json,
            }
            loader_fn = loader_map.get(src_type)
            if loader_fn is None:
                logger.warning("Unknown inventory source type '%s', skipping.", src_type)
                continue

            records = loader_fn(src_path)
            # Attach any per-source mapping rules for the resolver
            mapping_rules = source.get("mapping_rules", {})
            if mapping_rules:
                for rec in records:
                    rec.setdefault("_mapping_rules", mapping_rules)

            all_records.extend(records)
            logger.debug("Loaded %d records from %s (%s)", len(records), src_path, src_type)

        return all_records

    # ------------------------------------------------------------------ #
    # String-based helpers (for testing / embedding)
    # ------------------------------------------------------------------ #

    @staticmethod
    def load_yaml_string(content: str) -> list[dict[str, Any]]:
        """Load YAML inventory from a string (useful for tests)."""
        data = yaml.safe_load(content)
        records: list[dict[str, Any]] = []
        if isinstance(data, list):
            records = [dict(r) for r in data if isinstance(r, dict)]
        elif isinstance(data, dict):
            for key in ("inventory_items", "components", "items"):
                if isinstance(data.get(key), list):
                    records = [dict(r) for r in data[key] if isinstance(r, dict)]
                    break
        for rec in records:
            rec.setdefault("_source", "yaml")
        return records

    @staticmethod
    def load_json_string(content: str) -> list[dict[str, Any]]:
        """Load JSON inventory from a string (useful for tests)."""
        payload: Any = json.loads(content)
        raw: list[Any] = payload if isinstance(payload, list) else payload.get("items", [payload])
        return [{**item, "_source": "json"} for item in raw if isinstance(item, dict)]

    @staticmethod
    def load_csv_string(content: str) -> list[dict[str, Any]]:
        """Load CSV inventory from a string (useful for tests)."""
        reader = csv.DictReader(StringIO(content))
        return [{**row, "_source": "csv"} for row in reader]
