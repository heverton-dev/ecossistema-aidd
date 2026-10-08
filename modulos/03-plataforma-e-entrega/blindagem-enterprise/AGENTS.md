# Blindagem Enterprise — Slice Rules and Invariants

Tool rules: [`aidd-enterprise/AGENTS.md`](aidd-enterprise/AGENTS.md). Public API: `interface.py`.

## Slice rules

- Entry: `python ecossistema.py enterprise <args>` (e.g. `enterprise inject skill <name>`).
- Injected components carry a SHA-256 seal; never edit an injected copy, fix the canonical piece.
- `src/core` is a vendored copy of `componentes/compartilhado/src-core` (G_DRIFT_NUCLEO_COMPARTILHADO).
- Platform gates shared with master/ops: `modulos/03-plataforma-e-entrega/gates/`.

## Shared invariants

- Root `AGENTS.md` laws apply. Contract C1: no private API key; the host harness is the LLM (delegated protocol).
- Boundary (G_MODULO_FRONTEIRA): other slices import only this slice's `interface.py`; this slice imports others only through theirs.
- Tests never write inside `modulos/` or the real repo tree; use `tmp_path`.
- TDD: failing test first (exit 1), then green (exit 0). Zero stubs.
- Gate owners: `modulos/04-nucleo-compartilhado/contracts/MAPA-GATES.json`. Changed files trigger this slice's micro-gate (`scripts/micro_gates.py`).
- Query this slice's codebase-memory subgraph before grep or full reads.
