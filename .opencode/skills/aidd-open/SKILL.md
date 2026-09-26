---
name: aidd-open
description: Runs Triad Flow 02 (open-source engines) end to end - curates tested open-source engines, integrates them as VSA slices through aidd-factory, then master, enterprise and ops. Use when the user wants an app built on open-source engines, or types "/open", "/aidd-open", "open", "criar com open-source", "integrar motor open source", "gerar app via factory".
---

# aidd-open (Flow 02, open-source engines)

Pipeline: `[FORGE -> PLANNER] -> FACTORY -> [MASTER -> ENTERPRISE -> OPS]`

| Stage | Tool | Output |
|---|---|---|
| Foundation | `aidd-forge` | agentic governance and hooks |
| Planning | `aidd-planner` | integrations and requirements |
| Engine | `aidd-factory` | curated engines, multi-service compose, OpenAPI contracts |
| Harmonization | `aidd-master` | Modular Monolith VSA + Next.js |
| Shielding | `aidd-enterprise` | SHA-256 audit of proxies and gateways |
| Infrastructure | `aidd-ops` | isolated networks and native compose |

Namespace note: Antigravity CLI (`agy`) reserves `/open` to open files. There, use `/aidd-open` or `/factory`.

## Steps

1. Agree with the user on the reference open-source engines, routes and integration requirements. Done when name and domain are known.
2. Simulate first:
   ```bash
   python ecossistema.py open "My ERP" saas --dry-run
   ```
3. Run:
   ```bash
   python ecossistema.py open "My ERP" saas
   # explicit flags
   python ecossistema.py open --nome "My ERP" --slug my-erp --dominio saas --pasta ./projetos/my-erp
   # same engine
   python ecossistema.py run-fluxo --fluxo open --nome "My ERP" --slug my-erp --dominio saas --pasta ./projetos/my-erp
   ```
   Positional form: `<name> [domain]`. Done when the command exits 0.
4. Confirm the delivery honors the Quarteto Sine Qua Non defined in `AGENTS.md` section 3.

## Engine invariants (`run-fluxo`)

- Synchronous: no stage starts before the previous one exits 0.
- Handoffs validated by JSON Schema (`componentes/compartilhado/specs/handoff-*.schema.json`).
- Fail-fast: any gate break stops the pipeline.
- Writes `ORQUESTRACAO_EXECUCAO.json` in the target folder.
