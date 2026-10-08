# Fluxo 03 (Freedom) — Slice Rules and Invariants

Tool rules: [`core/aidd-freedom/AGENTS.md`](core/aidd-freedom/AGENTS.md). Public API: `interface.py`.

## Slice rules

- Entry: `python ecossistema.py freedom` (full flow) or `freedom-motor scan|convert-db|merge|pack`.
- Zero vendor lock-in: Supabase becomes pure PostgreSQL; writes to real accounts only with `--apply`.
- Local gates in `gates/`: G_ANT_LOCKIN_LEGADO, G_MIGRATION_ROT.

## Shared invariants

- Root `AGENTS.md` laws apply. Contract C1: no private API key; the host harness is the LLM (delegated protocol).
- Boundary (G_MODULO_FRONTEIRA): other slices import only this slice's `interface.py`; this slice imports others only through theirs.
- Tests never write inside `modulos/` or the real repo tree; use `tmp_path`.
- TDD: failing test first (exit 1), then green (exit 0). Zero stubs.
- Gate owners: `modulos/04-nucleo-compartilhado/contracts/MAPA-GATES.json`. Changed files trigger this slice's micro-gate (`scripts/micro_gates.py`).
- Query this slice's codebase-memory subgraph before grep or full reads.
