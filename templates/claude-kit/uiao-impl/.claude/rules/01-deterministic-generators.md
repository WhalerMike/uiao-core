# Rule: Deterministic Generators

**Always-on for `src/uiao_impl/generators/` and `src/uiao_impl/oscal/`.**

Generator output (OSCAL, SSP, POA&M, SAR, PPTX, docx, SBOM) must be byte-stable given the same inputs. This is enforced in tests (see `test_oscal_generate_plane.py`, `test_ssp_inject.py`, `test_poam.py`, `test_scuba_transformer_determinism.py`).

Common violations to avoid:

- `datetime.now()` in output — take `now` as a parameter from the caller.
- Dict/set iteration without `sorted()`.
- Pydantic `.dict()` without `sort_keys=True` in downstream `json.dumps`.
- `uuid.uuid4()` in content — derive a UUID5 from a stable namespace + content hash.
- Locale-dependent formatting (number formats, case folding).

When a generator needs a timestamp for the emitted artifact, accept `generated_at: datetime` as a parameter and default to `datetime.fromisoformat(os.environ.get("SOURCE_DATE_EPOCH", ...))` patterns — never `datetime.now()` baked in.
