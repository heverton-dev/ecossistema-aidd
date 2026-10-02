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
