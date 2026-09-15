# AIDD-Factory — Canonical Agent Directives & Factory Rules

> **Tool:** `aidd-factory`
> **Role:** Application Code & Integration Generator for Multi-Service Stacks.
> **Governance Standard:** Zero Stubs, Strict Determinism (Phases 1,4,5,6), LLM+Gates (Phases 2,3,7).

---

## 1. Core Execution Constraints

- **Thinking constraint:** Think strictly in compact English. Focus on template composition, schema validation, and integration contracts. Under 150 words.
- **Execution limit:** Resolve tasks in 3 to 5 discrete steps. Stop and request confirmation if more steps are required.
- **Output format:** Silent executor. Return code edits and 1-line execution status only.
- **Bash rule:** Always pipe verbose commands to tail/grep. E.g., `pytest tests/ 2>&1 | tail -n 25`.
- **Editing rule:** Use exact search/replace block edits (`replace_file_content`).

---

## 2. Factory Invariants & Quality Gates

1. **Single Input Contract (G_FACTORY_INPUT):** The factory consumes ONLY `PLANO-INFRAESTRUTURA.json` validated against `componentes/compartilhado/specs/plano-infraestrutura.schema.json`. Never read nicho catalogs directly — the plan is already resolved.
2. **Single Output Contract (G_FACTORY_OUTPUT):** The factory produces `FACTORY_OUTPUT.json` listing all generated artifacts with status. DeployOrchestrator consumes this.
3. **Deterministic Phases (G_FACTORY_DETERMINISTIC):** Phases 1, 4, 5, 6 are 100% deterministic (zero LLM). Phases 2, 3, 7 use LLM with AST+bandit gates.
4. **Zero Stubs:** All generators must produce real, functional code. No placeholders, no TODOs.
5. **Reuse Shared Components:** `result.py`, `escritor_atomico.py` from `componentes/compartilhado/src-core/`.

---

## 3. Command Dispatch

- `/factory [requirement]`: Orchestrates the factory pipeline via `python ecossistema.py factory [requirement]`.
- Phase-specific operations execute via deterministic CLI in `scripts/`.
