# Operações Ops — Slice Rules and Invariants

Tool rules: [`aidd-ops/AGENTS.md`](aidd-ops/AGENTS.md). Public API: `interface.py`.

## Slice rules

- Entry: `python ecossistema.py ops "<text>" --pasta <dest>`.
- Infra from catalog pieces only (`obter_peca`); idempotent hardening via Ansible `devsec.hardening`.
- Secrets only through sops + age; never plaintext in the repo.
- Platform gates shared with enterprise/master: `modulos/03-plataforma-e-entrega/gates/`.

## Shared invariants

- Root `AGENTS.md` laws apply. Contract C1: no private API key; the host harness is the LLM (delegated protocol).
- Boundary (G_MODULO_FRONTEIRA): other slices import only this slice's `interface.py`; this slice imports others only through theirs.
- Tests never write inside `modulos/` or the real repo tree; use `tmp_path`.
- TDD: failing test first (exit 1), then green (exit 0). Zero stubs.
- Gate owners: `modulos/04-nucleo-compartilhado/contracts/MAPA-GATES.json`. Changed files trigger this slice's micro-gate (`scripts/micro_gates.py`).
- Query this slice's codebase-memory subgraph before grep or full reads.
