---
name: aidd-pure
description: Runs Triad Flow 01 (build from scratch) end to end - forge, planner, generator with strict TDD Red-Green, then master, enterprise and ops. Use when the user wants a brand-new project from zero, or types "/pure", "pure", "criar projeto do zero", "projeto do zero puro", "novo projeto com TDD".
---

# aidd-pure (Flow 01, build from scratch)

Pipeline: `[FORGE -> PLANNER] -> GENERATOR -> [MASTER -> ENTERPRISE -> OPS]`

| Stage | Tool | Output |
|---|---|---|
| Foundation | `aidd-forge` | git hooks and isolation rules |
| Planning | `aidd-planner` | BDD/SDD entities, acceptance criteria, Quarteto Sine Qua Non |
| Engine | `aidd-generator` | strict TDD Red-Green, Clean Architecture in Python |
| Harmonization | `aidd-master` | Modular Monolith VSA + Next.js |
| Shielding | `aidd-enterprise` | SHA-256 injection and anti-drift audit |
| Infrastructure | `aidd-ops` | Dockerfile, Nginx SSL, compose |

## Steps

1. Collect or confirm name, slug, domain and destination folder with the user. Done when all four are known (slug and domain have defaults).
2. Simulate first:
   ```bash
   python ecossistema.py pure "My Project" gestao --dry-run
   ```
3. Run:
   ```bash
   python ecossistema.py pure "My Project" gestao
   # explicit flags
   python ecossistema.py pure --nome "My Project" --slug my-project --dominio gestao --pasta ./projetos/my-project
   # same engine
   python ecossistema.py run-fluxo --fluxo pure --nome "My Project" --slug my-project --dominio gestao --pasta ./projetos/my-project
   ```
   Positional form: `<name> [domain]`. Done when the command exits 0.
4. Confirm the delivery honors the Quarteto Sine Qua Non defined in `AGENTS.md` section 3 and a Next.js frontend.

## Engine invariants (`run-fluxo`)

- Synchronous: no stage starts before the previous one exits 0.
- Handoffs validated by JSON Schema (`componentes/compartilhado/specs/handoff-*.schema.json`).
- Fail-fast: any gate break stops the pipeline.
- Writes `ORQUESTRACAO_EXECUCAO.json` in the target folder.
