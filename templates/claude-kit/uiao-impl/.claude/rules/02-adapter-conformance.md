# Rule: Adapter Conformance

**Always-on for `src/uiao_impl/adapters/` and `adapters/`.**

Every adapter:

1. Inherits from a defined base (`adapters/base_adapter.py` for legacy, or the database/cloud-specific base in `src/uiao_impl/adapters/database_base.py`).
2. Passes `conformance_check.py` — run via `adapter-conformance.yml` in CI.
3. Has a behavioral test (`test_<vendor>_adapter_behavioral.py` or `test_<vendor>_adapter.py`) that exercises at least the golden path and one failure mode.
4. Has a fixture under `tests/fixtures/<vendor>-*.json` (or `.xml`, `.tf`, etc.) scrubbed of real secrets and customer data.
5. Emits evidence that validates against `uiao-core/schemas/ksi/evidence-bundle.schema.json`.
6. Registers a mapping in the IR layer if it feeds KSI evaluation (`src/uiao_impl/ir/`).

Parsers (e.g., `m365_parser.py`, `paloalto_parser.py`, `terraform_parser.py`, `vulnscan_parser.py`) stay pure: raw bytes → parsed model. No network, no environment reads. Network and auth belong in the adapter class.
