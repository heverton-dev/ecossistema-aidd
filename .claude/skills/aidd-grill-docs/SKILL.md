---
name: aidd-grill-docs
description: Socratic interview grounded in existing repository architecture, domain documentation, and invariant rules.
---

# AIDD-Grill-Docs — Architecture-Grounded Interview

Grounded variation of `aidd-grill` strictly anchored in the repository's documentation and architectural constraints.

## Execution Rules

1. **Context Ingestion:** Briefly inspect canonical project context files (`AGENTS.md`, `MEMORY.md`, and `docs/`) before querying.
2. **Ubiquitous Language:** Strictly enforce established domain terminology (e.g., Vertical Slice, Quality Gates, Harnesses, Result Monad).
3. **Detect Architectural Violations:** Interrogate any request threatening:
   - Inviolable Laws (Determinism, Zero Stubs, Extreme Token Economy).
   - Module isolation and bounded context boundaries.
   - Schema conventions, database WAL pragma, or API contract standards.
4. **Concrete Evidence Queries:** Cite specific documentation paths when highlighting discrepancies: *"Doc X establishes Y, but request proposes Z. Which direction takes precedence?"*.
5. **Completion Gate:** Once architectural compliance is verified, route directly to `/aidd-spec`.
