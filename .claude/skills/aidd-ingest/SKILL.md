---
name: aidd-ingest
description: Ingests external repositories (tools, skills, MCPs, processes), triages adherence against the 13 Inviolable Laws, runs the 4F audit pipeline, generates an evolution plan, and executes migration tickets in ephemeral worktrees. Use when the user wants to import, ingest, or adopt an external Git repository or tool into the ecosystem, or types "/ingest", "ingest", "ingerir repositorio", "adotar ferramenta externa".
---

# Ingestion & Harmonization Pipeline (`aidd-ingest`)

Executes the 4-phase canonical flow to adopt external codebases into the AIDD ecosystem with zero repository pollution and strict adherence to the 13 Inviolable Laws.

## Workflow

```
External Repo URL
       │
       ▼
Phase 1: Triage & Ephemeral Sandbox (`.tmp/ingest/<slug>/`)
       │
       ▼
Phase 2: 4F Audit Pipeline (`aidd-audit-4f`)
       │
       ▼
Phase 3: Evolution Plan Compilation (`PLANO-EVOLUCAO.json`)
       │
       ▼
Phase 4: Worktree Execution & Quality Gates (`aidd-evolution` / `ecossistema.py audit`)
```

### Phase 1: Triage & Sandbox Isolation

1. **Clone Sandbox:** Clone the target repository exclusively into `.tmp/ingest/<slug>/` (never inside tracked Git folders).
2. **Static Scan:**
   - Scan for adoptable assets: MCP servers, tool definitions, procedural skills, headless scripts.
   - Filter out violations: Stubs/mocks (Law #5), proprietary lock-in (Law #6), untracked subagents (Law #7), untested code (Laws #1 & #13).
3. **Generate Manifest:** Write `MANIFESTO-TRIAGEM.json` listing eligible components and discarded items with reasons.

### Phase 2: 4F Audit Pipeline

1. Pass the triage manifest to `aidd-audit-4f`.
2. Inspect eligible code against the 15 dimensions: typing, deterministic behavior, security, dependency hygiene.
3. Produce audit report in `docs/auditoria/<slug>/ciclo-01/RELATORIO-AUDITORIA.md`.

### Phase 3: Architecture & Evolution Plan

1. Map approved components to their single source of truth:
   - Skills: `componentes/compartilhado/skills/aidd-<name>/`
   - MCPs: `componentes/compartilhado/mcps/<name>/`
   - Gates: `gates/G_<NAME>.py`
2. Compile vertical slice tickets into `docs/auditoria/<slug>/ciclo-01/PLANO-EVOLUCAO.json` with binary definition of done (DoD).

### Phase 4: Worktree Execution & Convergence

1. Execute migration tickets in isolated ephemeral Git worktrees using `aidd-evolution`.
2. Enforce binary quality gate (`python ecossistema.py audit`) on every slice commit.
3. On human approval, merge worktree to target branch.
4. Run universal synchronization: `python ecossistema.py components sync --tipo todos`.
5. Purge the `.tmp/ingest/<slug>/` sandbox.

## Invariants

- **Zero Git Pollution:** Never commit raw external cloned repositories to the ecosystem.
- **Single Source of Truth:** All adopted pieces must land in `componentes/` first, then synced across harnesses.
- **Biting Gates:** Any new gate must prove it bites via automated failure tests (Law #13).
