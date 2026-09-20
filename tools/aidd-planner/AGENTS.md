# Canonical Directives: aidd-planner

> **Tool:** `aidd-planner`  
> **Mission:** Planning Engine, SDD/BDD Intake, and Fuel Generation for Canonical Triad (Flows 1, 2, 3).  
> **Target Schema:** `schemas/planner_schema.json`  

---

## 1. Architectural Invariants

1. **Zero Stubs Invariant:** Never produce `TODO`, `FIXME`, or placeholder tokens in `PLANNER.json`. All entities, endpoints, and BDD scenarios must be complete and typed.
2. **Quarteto Sine Qua Non:** Every generated plan must explicitly configure `/docs` (Swagger Studio), `/webhooks`, `/mcp`, and `/docs/guia` (key `guia`) with `ativo: true`.
3. **Strict Polymorphism:** `meta.fluxo_alvo` must strictly govern the structure of `payload_especifico_fluxo`.
4. **Binary Quality:** All plans must exit 0 on `G_PLANNER_SCHEMA.py`, `G_PLANNER_SINE_QUA_NON.py`, and `G_PLANNER_COERENCIA_FLUXO.py`.
5. **Factory Export = aidd-ops Envelope (Achado real 18/09/2026):** `export --formato factory` MUST return the exact `fase_1_intake`/`fase_2_curadoria`/`fase_3_sizing` envelope aidd-factory's `contrato_factory.py` validates against (`componentes/compartilhado/specs/plano-infraestrutura.schema.json`) — never a bespoke shape. `exportar_para_fluxo_factory` (`src/core/planner_engine.py`) reuses `aidd-ops`'s `pipeline_ops.montar_plano_em_memoria(texto, ferramentas_planejadas=payload_especifico_fluxo.ferramentas_opensource)` — the "nicho dinâmico" path (`tools/aidd-ops/AGENTS.md` §2.7) — instead of matching the 5 fixed catalog niches, since Lei #7 (Developer in Control) means the PRÉ-PLANO's own curated tool list is authoritative, not a keyword guess.

---

## 2. Dispatch Commands

- `init`: `python -m aidd_planner.cli init --fluxo <1|2|3> --nome <n> --pasta <p>`
- `validate`: `python -m aidd_planner.cli validate <caminho>`
- `export`: `python -m aidd_planner.cli export <caminho> --formato factory`
- `audit`: `python -m aidd_planner.cli audit <pasta>`
