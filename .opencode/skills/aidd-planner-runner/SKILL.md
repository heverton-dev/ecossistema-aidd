---
name: aidd-planner-runner
description: Generates and validates canonical SDD/BDD project blueprints and fuels the Triad flows (Generator, Factory, Bridge).
---

# AIDD-Planner Runner

Use this skill when the user wants to conduct architecture intake, generate a canonical `PLANNER.json` blueprint, or fuel any of the 3 Triad creation flows (Generator, Factory, Bridge). Trigger on mentions of 'planner', 'pre-plano', 'intake', 'blueprint', 'sdd', 'bdd', or 'spec driven'.

## Usage

```bash
# 1. Initialize a new PLANNER.json for Flow 1 (Generator), Flow 2 (Factory), or Flow 3 (Bridge)
python ecossistema.py planner init --fluxo <1|2|3> --nome "<Project Name>" --pasta <destination>

# 2. Validate an existing PLANNER.json
python ecossistema.py planner validate <path/to/PLANNER.json>

# 3. Export plan to downstream engine (e.g. aidd-factory)
python ecossistema.py planner export <path/to/PLANNER.json> --formato factory --saida <output.json>

# 4. Audit quality gates
python ecossistema.py planner audit <path/to/project>
```

## Supported Paradigms

- **SDD (Spec-Driven Development):** Governed by `schemas/planner_schema.json`.
- **BDD (Behavior-Driven Development):** Functional requirements in *Given / When / Then* format.
- **DDD (Domain-Driven Design):** Bounded contexts, domain entities, and invariants.
- **Quarteto Sine Qua Non:** Mandatory `/swagger`, `/webhooks`, `/mcp`, `/docs`.
- **Zero Stubs:** Binary verification against placeholders and incomplete specifications.

## Encadeamento Canônico de Intake
Após gerar e validar o blueprint `PLANNER.json`:
- **Próxima Skill:** `/aidd-dispatch-runner` (ou `python ecossistema.py dispatch --planner PLANNER.json`).
- **Fluxo Geral:** `/aidd-grill` ➔ `/aidd-spec` ➔ `/aidd-planner` ➔ `/aidd-dispatch-runner` ➔ `aidd-master`.

