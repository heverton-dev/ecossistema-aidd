# AIDD-Open — Canonical Agent Directives & Factory Rules

> **Tool:** `aidd-open`
> **Role:** Application Code & Integration Generator for Multi-Service Stacks.
> **Governance Standard:** Zero Stubs, Strict Determinism (Phases 1,4,5,6), LLM+Gates (Phases 2,3,7).

---

## 1. Core Execution Constraints

- Root `AGENTS.md` §1 governs execution (compact thinking, 3-5 steps, silent executor, piped bash, exact edits).
- Tool focus: template composition, schema validation, and integration contracts.

---

## 2. Factory Invariants & Quality Gates

1. **Single Input Contract (G_FACTORY_INPUT):** The factory consumes ONLY `PLANO-INFRAESTRUTURA.json` validated against `componentes/compartilhado/specs/plano-infraestrutura.schema.json`. Never read nicho catalogs directly — the plan is already resolved.
   - **Nicho dinâmico:** `fase_1_intake.saida.nicho_slug` may carry the `dinamico_` prefix (see `aidd-ops/scripts/phases_ops/01_intake.py::eh_nicho_dinamico`) for business domains outside the 5 fixed catalog niches (`clinicas`, `delivery`, `farmacias`, `b2b_industrial`, `energia_solar`). `01_analisador.py` detects this and synthesizes `blocos`/`bancos_logicos` from the plan's own `ferramentas` list (baseline `traefik` + conditional `postgres`) instead of requiring `templates/infra/nichos/<slug>.json` to exist. This is the deterministic subset of the "Discovery Engine" gap documented in `docs/features/v2_arquitetura-aidd-ops-factory.md` §7.1/§9.1 — a full GitHub-search engine remains future work.
2. **Single Output Contract (G_FACTORY_OUTPUT):** The factory produces `FACTORY_OUTPUT.json` listing all generated artifacts with status. DeployOrchestrator consumes this.
3. **Deterministic Phases (G_FACTORY_DETERMINISTIC):** Phases 1, 4, 5, 6 are 100% deterministic (zero LLM). Phases 2, 3, 7 use LLM with AST+bandit gates.
4. **Zero Stubs:** All generators must produce real, functional code. No placeholders, no TODOs.
5. **Reuse Shared Components:** `result.py`, `escritor_atomico.py` from `componentes/compartilhado/src-core/`.

---

## 3. Command Dispatch

- `/factory [requirement]`: Orchestrates the factory pipeline via `python ecossistema.py factory [requirement]`.
- Phase-specific operations execute via deterministic CLI in `scripts/`.
