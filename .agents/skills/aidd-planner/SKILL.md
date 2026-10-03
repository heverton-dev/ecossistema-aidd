---
name: aidd-planner
description: Generates and validates the canonical SDD/BDD app blueprint (PLANNER.json) that fuels the Triad flows (Generator, Factory, Bridge). Use when the user wants architecture intake, a project blueprint or a spec for a new app, or says "planner", "pré-plano", "intake", "blueprint", "SDD", "BDD". Not for ecosystem improvement plans in docs/planos/ (that is aidd-plan).
---

# aidd-planner

Owns `PLANNER.json`, the blueprint of the app to be built. Ecosystem improvement plans live in `aidd-plan`.

## Run

```bash
# 1. New PLANNER.json for Flow 1 (Generator), 2 (Factory) or 3 (Bridge)
python ecossistema.py planner init --fluxo <1|2|3> --nome "<Project Name>" --pasta <destination>

# 2. Validate
python ecossistema.py planner validate <path/to/PLANNER.json>

# 3. Export to a downstream engine (e.g. aidd-open)
python ecossistema.py planner export <path/to/PLANNER.json> --formato factory --saida <output.json>

# 4. Audit quality gates
python ecossistema.py planner audit <path/to/project>
```

Done when: `planner validate` exits 0.

## Paradigms

- **SDD:** governed by `schemas/planner_schema.json`.
- **BDD:** functional requirements as Given / When / Then.
- **DDD:** bounded contexts, entities, invariants.
- **Quarteto Sine Qua Non:** mandatory `/swagger`, `/webhooks`, `/mcp`, `/docs`.
- **Zero stubs:** binary check against placeholders and incomplete specs.

## Next step

After a valid `PLANNER.json`: `/aidd-dispatch` (or `python ecossistema.py dispatch --planner PLANNER.json`).
Chain: `/aidd-grill` -> `/aidd-spec` -> `/aidd-planner` -> `/aidd-dispatch` -> `aidd-master`.

## Negative Guardrails

- NEVER write a `PLANNER.json` under `docs/planos/` or put ecosystem improvement plans in one: those belong to `aidd-plan`.
- NEVER omit `--dominio` and `--slug` on `planner init`: missing values silently become `logistica` and a slug derived from the name.
- NEVER add `--force` over an existing `PLANNER.json` without user OK: it replaces the reviewed blueprint with a fresh template.
- NEVER hand-edit `HANDOFF_PLANNER_ENGINE.json` (contract C2): `run-fluxo` checks it against `componentes/compartilhado/specs/handoff-planner-to-engine.schema.json` and records its sha256; only `planner init` writes it.
- NEVER edit `tools/aidd-planner/schemas/planner_schema.json` to make `planner validate` pass; fix the blueprint.
- NEVER fill requirements with TODO or placeholder text to pass validation; `tools/aidd-planner/gates/G_PLANNER_SINE_QUA_NON.py` treats stubs as failure.

## Failure Modes & Fallback

- **`planner init` exits 1 ("já existe"):** show the user the existing `PLANNER.json`; rerun with another `--pasta`, or with `--force` only after explicit OK.
- **`planner validate` exits 1:** map each listed error to `tools/aidd-planner/schemas/planner_schema.json`, fix the field in `PLANNER.json`, validate again. After 3 failed rounds, stop and show the errors to the user.
- **"A planta nao pode ser desenhada":** the forge contract C1 (`.aidd/HANDOFF_FORGE_PLANNER.json`) is invalid; rerun `python ecossistema.py forge init <pasta>`, then `planner init`.
- **Quarteto missing in `planner audit <pasta>`:** add `/swagger`, `/webhooks`, `/mcp` and `/docs` to the blueprint, then rerun the audit.

## Stopping Checklist

- [ ] `python ecossistema.py planner validate <pasta>/PLANNER.json > pval.log 2>&1; echo $? > pval.rc` and `pval.rc` holds `0`.
- [ ] `python tools/aidd-planner/gates/G_PLANNER_SCHEMA.py <pasta> > pschema.log 2>&1; echo $? > pschema.rc` holds `0`.
- [ ] `python tools/aidd-planner/gates/G_PLANNER_SINE_QUA_NON.py <pasta> > psqn.log 2>&1; echo $? > psqn.rc` holds `0`.
- [ ] `python tools/aidd-planner/gates/G_PLANNER_COERENCIA_FLUXO.py <pasta> > pflow.log 2>&1; echo $? > pflow.rc` holds `0` (`--fluxo` matches the flow the user chose).
- [ ] `HANDOFF_PLANNER_ENGINE.json` and `DESIGN-SYSTEM.json` exist next to `PLANNER.json`.
