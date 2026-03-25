"""Tests for data/control-library/ YAML files."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

CONTROL_LIBRARY_DIR = Path(__file__).resolve().parent.parent / "data" / "control-library"
SC8_PATH = CONTROL_LIBRARY_DIR / "SC-8.yml"
IA2_PATH = CONTROL_LIBRARY_DIR / "IA-2.yml"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


# ---------------------------------------------------------------------------
# SC-8.yml tests
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def sc8() -> dict:
    return yaml.safe_load(SC8_PATH.read_text())


class TestSC8FileExists:
    def test_file_exists(self):
        assert SC8_PATH.exists(), "data/control-library/SC-8.yml must exist"

    def test_is_valid_yaml(self, sc8):
        assert isinstance(sc8, dict)


class TestSC8RequiredFields:
    def test_control_id(self, sc8):
        assert sc8["control_id"] == "SC-8"

    def test_title(self, sc8):
        assert sc8["title"] == "Transmission Confidentiality and Integrity"

    def test_status_implemented(self, sc8):
        assert sc8["status"] == "implemented"

    def test_narrative_present(self, sc8):
        assert "narrative" in sc8
        assert len(sc8["narrative"]) > 0


class TestSC8Narrative:
    def test_narrative_references_tls(self, sc8):
        narrative = sc8["narrative"].lower()
        assert "tls" in narrative

    def test_narrative_references_fips_140_2(self, sc8):
        narrative = sc8["narrative"]
        assert "FIPS 140-2" in narrative

    def test_narrative_references_tls_12(self, sc8):
        narrative = sc8["narrative"]
        assert "TLS 1.2" in narrative

    def test_narrative_has_jinja2_org_name(self, sc8):
        narrative = sc8["narrative"]
        assert "{{ organization.name }}" in narrative


class TestSC8ImplementedBy:
    def test_implemented_by_present(self, sc8):
        assert "implemented-by" in sc8
        assert isinstance(sc8["implemented-by"], list)
        assert len(sc8["implemented-by"]) >= 2

    def test_tls_termination_layer_present(self, sc8):
        types = [entry["type"] for entry in sc8["implemented-by"]]
        assert "TLSTerminationLayer" in types

    def test_api_gateway_present(self, sc8):
        types = [entry["type"] for entry in sc8["implemented-by"]]
        assert "APIGateway" in types

    def test_each_entry_has_description(self, sc8):
        for entry in sc8["implemented-by"]:
            assert "description" in entry
            assert len(entry["description"]) > 0


class TestSC8Evidence:
    def test_evidence_present(self, sc8):
        assert "evidence" in sc8
        assert isinstance(sc8["evidence"], list)
        assert len(sc8["evidence"]) >= 1

    def test_tls_compliance_scan_artifact(self, sc8):
        artifacts = [e["artifact"] for e in sc8["evidence"]]
        assert "tls-compliance-scan" in artifacts


# ---------------------------------------------------------------------------
# IA-2.yml existence and structure
# ---------------------------------------------------------------------------

def test_ia2_file_exists():
    assert IA2_PATH.exists(), f"Expected {IA2_PATH} to exist"


def test_ia2_yaml_is_valid():
    data = load_yaml(IA2_PATH)
    assert isinstance(data, dict)


def test_ia2_required_fields():
    data = load_yaml(IA2_PATH)
    assert data.get("control_id") == "IA-2"
    assert data.get("title") == "Identification and Authentication (Organizational Users)"
    assert data.get("status") == "implemented"
    assert "narrative" in data
    assert "implemented_by" in data
    assert "evidence" in data


def test_ia2_implemented_by_contains_abstract_types():
    data = load_yaml(IA2_PATH)
    implemented_by = data.get("implemented_by", [])
    assert "IdentityProvider" in implemented_by
    assert "PIVAuthenticationService" in implemented_by


def test_ia2_evidence_contains_mfa_enrollment_report():
    data = load_yaml(IA2_PATH)
    evidence = data.get("evidence", [])
    assert "mfa-enrollment-report" in evidence


def test_ia2_narrative_references_mfa():
    data = load_yaml(IA2_PATH)
    narrative = data.get("narrative", "")
    assert "MFA" in narrative or "multi-factor" in narrative.lower()


def test_ia2_narrative_references_piv_cac():
    data = load_yaml(IA2_PATH)
    narrative = data.get("narrative", "")
    assert "PIV" in narrative
    assert "CAC" in narrative


def test_ia2_jinja2_template_variables():
    """Narrative must contain Jinja2 template variables for organization.name
    and parameters['mfa-requirement'] (bracket notation, gold standard)."""
    data = load_yaml(IA2_PATH)
    narrative = data.get("narrative", "")
    assert "{{ organization.name }}" in narrative
    assert "{{ parameters['mfa-requirement'] }}" in narrative


def test_ia2_has_related_controls():
    data = load_yaml(IA2_PATH)
    assert "related_controls" in data
    assert isinstance(data["related_controls"], list)
    assert len(data["related_controls"]) >= 3


def test_ia2_parameters_have_descriptions():
    data = load_yaml(IA2_PATH)
    for param in data.get("parameters", []):
        assert "description" in param, f"Parameter {param.get('id')} missing description"
        assert len(param["description"]) > 0


def test_ia2_narrative_has_bold_section_headers():
    data = load_yaml(IA2_PATH)
    narrative = data.get("narrative", "")
    bold_count = narrative.count("**")
    # Each bold header uses opening and closing **, so at least 4 headers = 8 occurrences
    assert bold_count >= 8, "Narrative should have at least 4 bold section headers"


# ---------------------------------------------------------------------------
# SC-12.yml — Cryptographic Key Establishment and Management
# ---------------------------------------------------------------------------

SC12_PATH = CONTROL_LIBRARY_DIR / "SC-12.yml"


def test_sc12_file_exists():
    assert SC12_PATH.exists(), f"Expected {SC12_PATH} to exist"


def test_sc12_yaml_is_valid():
    data = load_yaml(SC12_PATH)
    assert isinstance(data, dict)


def test_sc12_required_fields():
    data = load_yaml(SC12_PATH)
    assert data.get("control_id") == "SC-12"
    assert data.get("title") == "Cryptographic Key Establishment and Management"
    assert data.get("status") == "implemented"
    assert "narrative" in data
    assert "implemented_by" in data
    assert "evidence" in data
    assert "parameters" in data
    assert "related_controls" in data


def test_sc12_implemented_by_contains_key_management():
    data = load_yaml(SC12_PATH)
    assert "KeyManagementService" in data["implemented_by"]


def test_sc12_evidence_contains_key_inventory():
    data = load_yaml(SC12_PATH)
    assert "key-inventory-report" in data["evidence"]


def test_sc12_narrative_references_fips_140():
    narrative = load_yaml(SC12_PATH).get("narrative", "")
    assert "FIPS 140-2" in narrative


def test_sc12_narrative_has_jinja2_org_name():
    narrative = load_yaml(SC12_PATH).get("narrative", "")
    assert "{{ organization.name }}" in narrative


def test_sc12_narrative_uses_bracket_param_syntax():
    narrative = load_yaml(SC12_PATH).get("narrative", "")
    assert "{{ parameters['" in narrative


# ---------------------------------------------------------------------------
# AT-3.yml — Role-Based Training
# ---------------------------------------------------------------------------

AT3_PATH = CONTROL_LIBRARY_DIR / "AT-3.yml"


def test_at3_file_exists():
    assert AT3_PATH.exists(), f"Expected {AT3_PATH} to exist"


def test_at3_yaml_is_valid():
    data = load_yaml(AT3_PATH)
    assert isinstance(data, dict)


def test_at3_required_fields():
    data = load_yaml(AT3_PATH)
    assert data.get("control_id") == "AT-3"
    assert data.get("title") == "Role-Based Training"
    assert data.get("status") == "implemented"
    assert "narrative" in data
    assert "implemented_by" in data
    assert "evidence" in data
    assert "parameters" in data
    assert "related_controls" in data


def test_at3_implemented_by_contains_lms():
    data = load_yaml(AT3_PATH)
    assert "LearningManagementSystem" in data["implemented_by"]


def test_at3_evidence_contains_training_report():
    data = load_yaml(AT3_PATH)
    assert "role-based-training-completion-report" in data["evidence"]


def test_at3_narrative_has_jinja2_org_name():
    narrative = load_yaml(AT3_PATH).get("narrative", "")
    assert "{{ organization.name }}" in narrative


def test_at3_narrative_uses_bracket_param_syntax():
    narrative = load_yaml(AT3_PATH).get("narrative", "")
    assert "{{ parameters['" in narrative


# ---------------------------------------------------------------------------
# SI-4.yml — System Monitoring
# ---------------------------------------------------------------------------

SI4_PATH = CONTROL_LIBRARY_DIR / "SI-4.yml"


def test_si4_file_exists():
    assert SI4_PATH.exists(), f"Expected {SI4_PATH} to exist"


def test_si4_yaml_is_valid():
    data = load_yaml(SI4_PATH)
    assert isinstance(data, dict)


def test_si4_required_fields():
    data = load_yaml(SI4_PATH)
    assert data.get("control_id") == "SI-4"
    assert data.get("title") == "System Monitoring"
    assert data.get("status") == "implemented"
    assert "narrative" in data
    assert "implemented_by" in data
    assert "evidence" in data
    assert "parameters" in data
    assert "related_controls" in data


def test_si4_implemented_by_contains_telemetry():
    data = load_yaml(SI4_PATH)
    assert "TelemetryPlane" in data["implemented_by"]


def test_si4_evidence_contains_siem_report():
    data = load_yaml(SI4_PATH)
    assert "siem-alert-summary-report" in data["evidence"]


def test_si4_narrative_has_jinja2_org_name():
    narrative = load_yaml(SI4_PATH).get("narrative", "")
    assert "{{ organization.name }}" in narrative


def test_si4_narrative_uses_bracket_param_syntax():
    narrative = load_yaml(SI4_PATH).get("narrative", "")
    assert "{{ parameters['" in narrative
