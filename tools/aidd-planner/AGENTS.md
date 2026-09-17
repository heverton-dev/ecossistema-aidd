# Canonical Directives: aidd-planner

> **Tool:** `aidd-planner`  
> **Mission:** Planning Engine, SDD/BDD Intake, and Fuel Generation for Canonical Triad (Flows 1, 2, 3).  
> **Target Schema:** `schemas/planner_schema.json`  

---

## 1. Architectural Invariants

1. **Zero Stubs Invariant:** Never produce `TODO`, `FIXME`, or placeholder tokens in `PLANNER.json`. All entities, endpoints, and BDD scenarios must be complete and typed.
2. **Quarteto Sine Qua Non:** Every generated plan must explicitly configure `/swagger`, `/webhooks`, `/mcp`, and `/docs` with `ativo: true`.
3. **Strict Polymorphism:** `meta.fluxo_alvo` must strictly govern the structure of `payload_especifico_fluxo`.
4. **Binary Quality:** All plans must exit 0 on `G_PLANNER_SCHEMA.py`, `G_PLANNER_SINE_QUA_NON.py`, and `G_PLANNER_COERENCIA_FLUXO.py`.

---

## 2. Dispatch Commands

- `init`: `python -m aidd_planner.cli init --fluxo <1|2|3> --nome <n> --pasta <p>`
- `validate`: `python -m aidd_planner.cli validate <caminho>`
- `export`: `python -m aidd_planner.cli export <caminho> --formato factory`
- `audit`: `python -m aidd_planner.cli audit <pasta>`
