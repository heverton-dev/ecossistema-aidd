# Fluxo 01 (Pure) — Slice Rules and Invariants

Tool rules: [`core/aidd-pure/AGENTS.md`](core/aidd-pure/AGENTS.md). Public API: `interface.py`.

## Slice rules

- Entry: `python ecossistema.py pure` (full flow) or `pure-motor "<idea>"` (8-phase engine only).
- Local gates in `gates/`: G_STACK_PADRAO_OURO, G_FRONTEND_LAYERS, G_NOVE_CAMADAS_MERCADO, G_TEMPLATE_TANSTACK_OFFLINE, G_PROTOTYPE_REWRITE.
- Generated projects follow the gold-standard stack (TanStack Start, React, Tailwind PWA).

## Shared invariants

- Root `AGENTS.md` laws apply. Contract C1: no private API key; the host harness is the LLM (delegated protocol).
- Boundary (G_MODULO_FRONTEIRA): other slices import only this slice's `interface.py`; this slice imports others only through theirs.
- Tests never write inside `modulos/` or the real repo tree; use `tmp_path`.
- TDD: failing test first (exit 1), then green (exit 0). Zero stubs.
- Gate owners: `modulos/04-nucleo-compartilhado/contracts/MAPA-GATES.json`. Changed files trigger this slice's micro-gate (`scripts/micro_gates.py`).
- Query this slice's codebase-memory subgraph before grep or full reads.
