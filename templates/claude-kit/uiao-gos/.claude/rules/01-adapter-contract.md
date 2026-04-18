# Rule: Adapter Contract

**Always-on for code in `core/providers/` and `core/adapters/`.**

Every adapter:

1. Subclasses `BaseAdapter` from `core/providers/base_adapter.py`.
2. Implements `collect() -> Evidence` deterministically. Given the same input state, the same bytes out.
3. Declares `adapter_id`, `vendor`, `version` as class attributes — must match a row in `uiao-core/canon/adapter-registry.yaml`.
4. Registers itself in `core/providers/provider_registry.py` (or IPAM registry for IPAM adapters).
5. Exports a manifest `adapter-manifest.json` in its directory, validating against `uiao-core/schemas/adapter-registry/adapter-registry.schema.json`.

Evidence emitted must validate against `uiao-core/schemas/ksi/evidence-bundle.schema.json`.

Do not add state to `BaseAdapter`. Adapters are stateless per invocation.

Concurrency: adapters must be safe under `asyncio.gather` — no module-level mutable state.
