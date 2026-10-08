# Fluxo 02 (Open) — Slice Rules and Invariants

Tool rules: [`core/aidd-open/AGENTS.md`](core/aidd-open/AGENTS.md). Public API: `interface.py`.

## Slice rules

- Entry: `python ecossistema.py open` (full flow) or `open-motor --plano <file> --pasta <dest>`.
- Single input: `PLANO-INFRAESTRUTURA.json` validated by schema; single output: `FACTORY_OUTPUT.json`.
- Local gates in `gates/`: G_COMPONENTE_AGNOSTICO, G_HADOLINT.

## Shared invariants

- Root `AGENTS.md` laws apply. Contract C1: no private API key; the host harness is the LLM (delegated protocol).
- Boundary (G_MODULO_FRONTEIRA): other slices import only this slice's `interface.py`; this slice imports others only through theirs.
- Tests never write inside `modulos/` or the real repo tree; use `tmp_path`.
- TDD: failing test first (exit 1), then green (exit 0). Zero stubs.
- Gate owners: `modulos/04-nucleo-compartilhado/contracts/MAPA-GATES.json`. Changed files trigger this slice's micro-gate (`scripts/micro_gates.py`).
- Query this slice's codebase-memory subgraph before grep or full reads.
