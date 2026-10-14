---
name: aidd-planner
description: Generates and validates the canonical SDD/BDD app blueprint (PLANNER.json) that fuels the Triad flows (Generator, Factory, Bridge). Use when the user wants architecture intake, a project blueprint or a spec for a new app, or says "planner", "pré-plano", "intake", "blueprint", "SDD", "BDD". Not for ecosystem improvement plans in docs/planos/ (that is aidd-plan).
---

# aidd-planner

Owns `PLANNER.json`, the blueprint of the app to be built. Ecosystem improvement plans live in `aidd-plan`.

## Run

The planner opens in this order. Each step blocks the next until it exits 0.

```bash
# 0. Environment (Mobbin path + deploy variables). Mobbin paths, in this order:
#    1 = official MCP (the harness uses it), 2 = MOBBIN_API_KEY in .env, 3 = none.
python ecossistema.py planner ambiente --pasta <destination> --mobbin <1|2|3>

# 1. Interview and spec, written by the harness (never an API key), saved under the project:
#    <destination>/.aidd/intake/grill.md  (/aidd-grill: must ask tone, color, references, audience)
#    <destination>/.aidd/intake/spec.md   (/aidd-spec: needs a "### Visual Direction" block with
#                                          tom, cor_primaria (#RRGGBB), referencias, publico)
python ecossistema.py planner entrevista --pasta <destination> --modo <interativo|autonomo>

# 2. New PLANNER.json for Flow 1 (Generator), 2 (Factory) or 3 (Bridge)
python ecossistema.py planner init --fluxo <1|2|3> --nome "<Project Name>" --pasta <destination>

# 3. Validate
python ecossistema.py planner validate <path/to/PLANNER.json>

# 4. Export to a downstream engine (e.g. aidd-open)
python ecossistema.py planner export <path/to/PLANNER.json> --formato factory --saida <output.json>

# 5. Audit quality gates
python ecossistema.py planner audit <path/to/project>
```

Done when: `planner validate` exits 0.

## Environment, Mobbin and interview

- **Environment** blocks `planner init` unless the Mobbin path is recorded in `.aidd/ambiente.json` (no secrets) and
  these deploy variables are in `.env`: `VPS_HOST`, `VPS_USER`, `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ZONE_ID`,
  `DEFAULT_ROOT_DOMAIN` and `SSH_KEY_PATH` or `VPS_PASSWORD` (deploy is compose-native only). Mobbin never blocks.
- **Path 1 (MCP):** the harness runs the official Mobbin MCP (OAuth in the browser, per client) and writes
  `.aidd/intake/referencias-mcp.json` (screens and flows). **Path 2 (key):** the planner queries the REST API once
  per screen type from the spec (mode `standard`, cached under `.aidd/cache/mobbin/`). **Path 3:** the spec only.
- `planner init` writes `referencias-ui.json` (derived tokens and links only, never images) and a `DESIGN-SYSTEM.json`
  whose primary color is the `cor_primaria` of the spec. If Mobbin fails it falls back to the spec with a warning.
- `--modo autonomo` records that the interview ran without the user in the chat: say so in the stage report.

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
- NEVER print, paste or commit a Mobbin or Cloudflare secret; the Environment step stores only names and choices.
- NEVER invent the interview answers as if the user gave them: in `--modo autonomo` write them as `Recommended: <answer>, because <reason>`.
- NEVER omit `--dominio` and `--slug` on `planner init`: missing values silently become `logistica` and a slug derived from the name.
- NEVER add `--force` over an existing `PLANNER.json` without user OK: it replaces the reviewed blueprint with a fresh template.
- NEVER hand-edit `HANDOFF_PLANNER_ENGINE.json` (contract C2): `run-fluxo` checks it against `componentes/compartilhado/specs/handoff-planner-to-engine.schema.json` and records its sha256; only `planner init` writes it.
- NEVER edit `modulos/01-governanca-e-qualidade/core/aidd-planner/schemas/planner_schema.json` to make `planner validate` pass; fix the blueprint.
- NEVER fill requirements with TODO or placeholder text to pass validation; `modulos/01-governanca-e-qualidade/core/aidd-planner/gates/G_PLANNER_SINE_QUA_NON.py` treats stubs as failure.

## Failure Modes & Fallback

- **`planner init` exits 1 ("já existe"):** show the user the existing `PLANNER.json`; rerun with another `--pasta`, or with `--force` only after explicit OK.
- **`planner validate` exits 1:** map each listed error to `modulos/01-governanca-e-qualidade/core/aidd-planner/schemas/planner_schema.json`, fix the field in `PLANNER.json`, validate again. After 3 failed rounds, stop and show the errors to the user.
- **`planner init` exits 1 ("Ambiente incompleto" / "Intake incompleto"):** run the step it names (`planner ambiente` or the interview) and retry; never edit `.aidd/ambiente.json` by hand.
- **"A planta nao pode ser desenhada":** the forge contract C1 (`.aidd/HANDOFF_FORGE_PLANNER.json`) is invalid; rerun `python ecossistema.py forge init <pasta>`, then `planner init`.
- **Quarteto missing in `planner audit <pasta>`:** add `/swagger`, `/webhooks`, `/mcp` and `/docs` to the blueprint, then rerun the audit.

## Stopping Checklist

- [ ] `python ecossistema.py planner validate <pasta>/PLANNER.json > pval.log 2>&1; echo $? > pval.rc` and `pval.rc` holds `0`.
- [ ] `python modulos/01-governanca-e-qualidade/core/aidd-planner/gates/G_PLANNER_SCHEMA.py <pasta> > pschema.log 2>&1; echo $? > pschema.rc` holds `0`.
- [ ] `python modulos/01-governanca-e-qualidade/core/aidd-planner/gates/G_PLANNER_SINE_QUA_NON.py <pasta> > psqn.log 2>&1; echo $? > psqn.rc` holds `0`.
- [ ] `python modulos/01-governanca-e-qualidade/core/aidd-planner/gates/G_PLANNER_COERENCIA_FLUXO.py <pasta> > pflow.log 2>&1; echo $? > pflow.rc` holds `0` (`--fluxo` matches the flow the user chose).
- [ ] `HANDOFF_PLANNER_ENGINE.json` and `DESIGN-SYSTEM.json` exist next to `PLANNER.json`.
