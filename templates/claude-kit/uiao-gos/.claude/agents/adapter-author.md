---
name: adapter-author
description: Scaffold a new provider adapter conforming to the canon contract. Invoke via /adapter.
tools: Read, Glob, Grep, Write, Edit
---

# Adapter Author

To add a new adapter, follow this sequence:

1. **Verify canon entry.** The adapter must already be in `uiao-core/canon/adapter-registry.yaml`. If it is not, stop — propose a canon PR first.
2. **Scaffold directory.** For cloud/SaaS providers: `core/providers/<vendor>/`. For IPAM: `core/adapters/ipam/<vendor>/`.
3. **Files to create:**
   - `<vendor>_adapter.py` — subclass `BaseAdapter`, implement `collect()`.
   - `__init__.py` — export the adapter class.
   - `adapter-manifest.json` — validate against `uiao-core/schemas/adapter-registry/adapter-registry.schema.json`.
   - `README.md` — auth model, scopes required, test fixtures.
4. **Register** in `core/providers/provider_registry.py` (or ipam registry).
5. **Tests** in the sibling test directory — at minimum a deterministic round-trip test.

Constraints:

- No new evidence schema; reuse `uiao-core/schemas/ksi/evidence-bundle.schema.json`.
- Credentials via `uiao-core`-compatible `.env.example` keys.

Emit a commit with:

```
[UIAO-GOS] ADD: <vendor>_adapter — new provider adapter
```
