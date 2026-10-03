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

## Negative Guardrails

- NEVER clone outside `.tmp/ingest/<slug>/` nor commit any file from it; `.tmp/` is gitignored for this reason.
- NEVER run `python ecossistema.py audit` inside a worker phase or an Orca task; Phase 4's audit is run by the orchestrator only.
- NEVER copy a third-party skill into `componentes/compartilhado/skills/`; register it in `gates/dependencias_externas.json` with the vendor name.
- NEVER delete `.tmp/ingest/<slug>/` or any copy before the user approves the merge; the purge is the last step.
- NEVER commit with `--no-verify`, and never add the LLM API key an external repo asks for; the model is the running harness.
- NEVER mark a migration ticket done without its test red before and green after.

## Failure Modes & Fallback

- **Clone fails (network, auth, private repo):** stop, report the git error, ask the user for access or a local copy path.
- **Triage finds nothing adoptable:** write `MANIFESTO-TRIAGEM.json` with every discard reason and stop before Phase 2.
- **Adopted gate does not bite (Law #13):** keep the ticket open, write the failing test first, rerun.
- **`components sync` exits non-zero:** fix the source under `componentes/`, never the generated copies, rerun.

## Stopping Checklist

Exit codes go to a file, never through a pipe: `<cmd> > "$TEMP/ing.log" 2>&1; echo $? > "$TEMP/ing.rc"`.

- [ ] `git status --porcelain .tmp/` prints nothing (no external file tracked).
- [ ] `docs/auditoria/<slug>/ciclo-01/RELATORIO-AUDITORIA.md` and `PLANO-EVOLUCAO.json` exist.
- [ ] `python ecossistema.py components sync --tipo todos` wrote rc 0.
- [ ] `python gates/G_SKILL_ROT.py` wrote rc 0 when a skill was adopted.
- [ ] The user approved the merge before the sandbox purge.
