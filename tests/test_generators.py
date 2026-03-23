"""End-to-end tests for migrated generators (ADR-0003).

Verifies that all generator modules can be imported and that their
core builder functions work with minimal/empty context data.
"""
import json


class TestGeneratorImports:
    """Verify all generator modules import cleanly."""

    def test_import_ssp(self):
        from uiao_core.generators import ssp
        assert hasattr(ssp, "build_ssp")
        assert hasattr(ssp, "load_context")
        assert hasattr(ssp, "build_set_parameters")

    def test_import_oscal(self):
        from uiao_core.generators import oscal
        assert hasattr(oscal, "build_oscal")
        assert hasattr(oscal, "build_component_definition")
        assert hasattr(oscal, "load_context")

    def test_import_poam(self):
        from uiao_core.generators import poam
        assert hasattr(poam, "build_poam_export")
        assert hasattr(poam, "build_poam")
        assert hasattr(poam, "detect_gaps")

    def test_import_docs(self):
        from uiao_core.generators import docs
        assert hasattr(docs, "build_docs")
        assert hasattr(docs, "load_canon")
        assert hasattr(docs, "load_data_files")

    def test_import_package_init(self):
        from uiao_core.generators import (
            build_docs,
            build_oscal,
            build_poam_export,
            build_ssp,
        )
        assert callable(build_ssp)
        assert callable(build_oscal)
        assert callable(build_poam_export)
        assert callable(build_docs)


class TestOSCALBuilder:
    """Test OSCAL component-definition builder with empty context."""

    def test_build_component_definition_empty(self):
        from uiao_core.generators.oscal import build_component_definition
        cd = build_component_definition({})
        assert "uuid" in cd
        assert "metadata" in cd
        assert "components" in cd
        assert isinstance(cd["components"], list)

    def test_build_component_definition_with_planes(self):
        from uiao_core.generators.oscal import build_component_definition
        context = {
            "control_planes": [
                {"id": "identity", "name": "Identity Plane", "description": "Test"},
            ],
            "unified_compliance_matrix": [],
        }
        cd = build_component_definition(context)
        assert len(cd["components"]) == 1
        assert cd["components"][0]["title"] == "Identity Plane"

    def test_build_component_definition_includes_core_stack(self):
        """core-stack.yml components appear in the OSCAL component definition."""
        from uiao_core.generators.oscal import build_component_definition
        context = {
            "control_planes": [],
            "unified_compliance_matrix": [],
            "core_stack": [
                {"id": "INR", "name": "Microsoft INR", "pillar": "identity"},
                {"id": "IB", "name": "Infoblox IPAM", "pillar": "addressing"},
                {"id": "CAT", "name": "Cisco Catalyst", "pillar": "overlay"},
            ],
        }
        cd = build_component_definition(context)
        titles = [c["title"] for c in cd["components"]]
        assert "Microsoft INR" in titles
        assert "Infoblox IPAM" in titles
        assert "Cisco Catalyst" in titles
        # Verify type is software and props contain core-stack-ref
        inr = next(c for c in cd["components"] if c["title"] == "Microsoft INR")
        assert inr["type"] == "software"
        prop_map = {p["name"]: p["value"] for p in inr["props"]}
        assert prop_map.get("core-stack-ref") == "INR"
        assert prop_map.get("pillar-ref") == "component-identity"
        assert prop_map.get("uiao-pillar") == "IDENTITY"


class TestPOAMBuilder:
    """Test POA&M gap detection and builder."""

    def test_detect_gaps_empty(self):
        from uiao_core.generators.poam import detect_gaps
        gaps = detect_gaps({})
        assert isinstance(gaps, list)
        assert len(gaps) == 0

    def test_detect_gaps_low_maturity(self):
        from uiao_core.generators.poam import detect_gaps
        context = {
            "unified_compliance_matrix": [
                {"category": "Access Control", "cisa_maturity": "Initial", "nist_controls": ["AC-1"]},
            ],
        }
        gaps = detect_gaps(context)
        assert len(gaps) >= 1
        assert "Low maturity" in gaps[0]["title"]

    def test_build_poam_empty(self):
        from uiao_core.generators.poam import build_poam
        poam = build_poam({})
        assert "uuid" in poam
        assert "metadata" in poam
        assert "poam-items" in poam


class TestSSPBuilder:
    """Test SSP builder with empty context."""

    def test_build_ssp_empty_context(self, tmp_path):
        from uiao_core.generators.ssp import build_ssp
        output = tmp_path / "ssp.json"
        _result = build_ssp(
            canon_path=tmp_path / "nonexistent.yaml",
            data_dir=tmp_path,
            output_path=output,
        )
        assert output.exists()
        with open(output) as f:
            data = json.load(f)
        assert "system-security-plan" in data

    def test_build_ssp_includes_core_stack_components(self, tmp_path):
        """core-stack.yml items appear as software components in the SSP."""
        import yaml
        from uiao_core.generators.ssp import build_ssp_skeleton
        core_stack = [
            {"id": "INR", "name": "Microsoft INR", "pillar": "identity"},
            {"id": "IB", "name": "Infoblox IPAM", "pillar": "addressing"},
        ]
        (tmp_path / "core-stack.yml").write_text(yaml.dump(core_stack))
        context = {"core_stack": core_stack, "inventory_items": [], "control_planes": [], "unified_compliance_matrix": []}
        ssp = build_ssp_skeleton(context)
        component_titles = [c["title"] for c in ssp["system-implementation"]["components"]]
        assert "Microsoft INR" in component_titles
        assert "Infoblox IPAM" in component_titles
        # Verify type and pillar props
        inr = next(c for c in ssp["system-implementation"]["components"] if c["title"] == "Microsoft INR")
        assert inr["type"] == "software"
        prop_names = {p["name"]: p["value"] for p in inr["props"]}
        assert prop_names.get("pillar") == "IDENTITY"
        assert prop_names.get("core-stack-ref") == "INR"
        assert prop_names.get("pillar-ref") == "component-identity"

    def test_inventory_items_linked_to_core_stack(self):
        """Inventory items get component-uuid links to both control plane and core-stack."""
        from uiao_core.generators.ssp import build_ssp_skeleton
        context = {
            "core_stack": [{"id": "INR", "name": "Microsoft INR", "pillar": "identity"}],
            "control_planes": [{"id": "identity", "name": "Identity Plane", "description": ""}],
            "inventory_items": [
                {
                    "id": "inv-entra-id",
                    "asset_type": "software",
                    "description": "Entra ID",
                    "responsible_party": "agency-admin",
                    "implemented_components": ["component-identity"],
                    "props": [],
                }
            ],
            "unified_compliance_matrix": [],
        }
        ssp = build_ssp_skeleton(context)
        inv_items = ssp["system-implementation"].get("inventory-items", [])
        assert len(inv_items) == 1
        impl_uuids = [ic["component-uuid"] for ic in inv_items[0]["implemented-components"]]
        # Must reference both the control-plane component and the core-stack component
        assert len(impl_uuids) == 2


class TestInventoryGapDetection:
    """Test POA&M inventory gap detection from core-stack.yml."""

    def test_detect_gaps_core_stack_no_inventory(self):
        """Core stack component with no inventory coverage creates a POA&M gap."""
        from uiao_core.generators.poam import detect_gaps
        context = {
            "core_stack": [{"id": "CAT", "name": "Cisco Catalyst", "pillar": "overlay"}],
            "inventory_items": [],  # no inventory for overlay
        }
        gaps = detect_gaps(context)
        titles = [g["title"] for g in gaps]
        assert any("No inventory coverage" in t and "Cisco Catalyst" in t for t in titles)

    def test_detect_gaps_core_stack_covered(self):
        """Core stack component with inventory coverage produces no inventory gap."""
        from uiao_core.generators.poam import detect_gaps
        context = {
            "core_stack": [{"id": "INR", "name": "Microsoft INR", "pillar": "identity"}],
            "inventory_items": [
                {
                    "id": "inv-entra",
                    "implemented_components": ["component-identity"],
                }
            ],
        }
        gaps = detect_gaps(context)
        inv_gaps = [g for g in gaps if "No inventory coverage" in g.get("title", "")]
        assert len(inv_gaps) == 0

    def test_build_poam_export_loads_poam_findings_yml(self, tmp_path):
        """build_poam_export merges entries from poam-findings.yml."""
        import yaml
        from uiao_core.generators.poam import build_poam_export
        findings = [
            {
                "title": "Test finding from YAML",
                "description": "A test finding",
                "severity": "high",
                "control-ids": ["AC-2"],
                "source": "manual-review",
            }
        ]
        # Write a minimal data dir with only poam-findings.yml
        (tmp_path / "poam-findings.yml").write_text(yaml.dump(findings))
        out_dir = tmp_path / "oscal"
        build_poam_export(
            canon_path=tmp_path / "nonexistent.yaml",
            data_dir=tmp_path,
            output_dir=out_dir,
        )
        with open(out_dir / "uiao-poam.json") as f:
            data = json.load(f)
        items = data["plan-of-action-and-milestones"]["poam-items"]
        titles = [it["title"] for it in items]
        assert "Test finding from YAML" in titles
