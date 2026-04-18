---
description: Index and sync appendices
argument-hint: "[--regenerate]"
---

Invoke the `appendix-manager` agent.

By default, runs in check-only mode: reports orphans, dangling references, and divergence between `uiao-core/appendices/` and `uiao-docs/appendices/`.

With `--regenerate` in `$ARGUMENTS`, regenerates the appendix index and commits with:

```
[UIAO-CORE] UPDATE: appendix-index — regenerate from <N> artifacts
```

Mirrors `.github/workflows/appendix-sync.yml` (lives in `uiao-docs`).
