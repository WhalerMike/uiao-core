# Rule: No-Hallucination Protocol

**Always-on.**

Use only provided text, synced canon, and cited sources as truth. Mark gaps as `MISSING`, uncertainty as `UNSURE`, new content as `NEW (Proposed)`.

Cite every canonical ID (control, KSI, adapter, ADR) against the synced canon under `canon/`. If the ID is not there, the canon sync may be stale — run `/canon-sync` before assuming it is missing.

Never reference a prior version of canon. One version at a time.
