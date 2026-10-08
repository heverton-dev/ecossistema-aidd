# Fatiamento Master — Slice Rules and Invariants

Tool rules: [`aidd-master/AGENTS.md`](aidd-master/AGENTS.md). Public API: `interface.py`.

## Slice rules

- Entry: `python ecossistema.py master <args>` (e.g. `master add-module <name>`).
- Modular monolith in vertical slices (VSA) with Clean Architecture; harmonizes the Quarteto (`/swagger`, `/webhooks`, `/mcp`, `/docs`).
- Join barrier `aidd-master/scripts/vsa_join_barrier.py` fails without micro-gates.
- Platform gates shared with enterprise/ops: `modulos/03-plataforma-e-entrega/gates/`.

## Shared invariants

- Root `AGENTS.md` laws apply. Contract C1: no private API key; the host harness is the LLM (delegated protocol).
- Boundary (G_MODULO_FRONTEIRA): other slices import only this slice's `interface.py`; this slice imports others only through theirs.
- Tests never write inside `modulos/` or the real repo tree; use `tmp_path`.
- TDD: failing test first (exit 1), then green (exit 0). Zero stubs.
- Gate owners: `modulos/04-nucleo-compartilhado/contracts/MAPA-GATES.json`. Changed files trigger this slice's micro-gate (`scripts/micro_gates.py`).
- Query this slice's codebase-memory subgraph before grep or full reads.
