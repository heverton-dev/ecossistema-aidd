---
name: aidd-open
description: Runs Triad Flow 02 (open-source engines) end to end - curates tested open-source engines, integrates them as VSA slices through the aidd-open engine, then master, enterprise and ops; also runs only the engine that generates a multi-service stack from a PLANO-INFRAESTRUTURA.json. Use when the user wants an app built on open-source engines or a deployable stack from an infrastructure plan, or types "/open", "/aidd-open", "open", "open-motor", "/factory", "factory", "criar com open-source", "integrar motor open source", "gerar stack", "gerar gateway", "gerar compose".
---

# aidd-open (Flow 02, open-source engines)

Pipeline: `[FORGE -> PLANNER] -> FACTORY -> [MASTER -> ENTERPRISE -> OPS]`

| Stage | Tool | Output |
|---|---|---|
| Foundation | `aidd-forge` | agentic governance and hooks |
| Planning | `aidd-planner` | integrations and requirements |
| Engine | `aidd-open` (`tools/aidd-open`) | curated engines, multi-service compose, OpenAPI contracts |
| Harmonization | `aidd-master` | Modular Monolith VSA + Next.js |
| Shielding | `aidd-enterprise` | SHA-256 audit of proxies and gateways |
| Infrastructure | `aidd-ops` | isolated networks and native compose |

Namespace note: Antigravity CLI (`agy`) reserves `/open` to open files. There, use `/aidd-open`.

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

## Engine only (`open-motor`)

Generates the multi-service stack (FastAPI gateway, Next.js whitelabel frontend, unified docker-compose, `init-multiple-databases.sh`, `.env` per service, webhooks, Swagger/OpenAPI, cross-service validation) from a `PLANO-INFRAESTRUTURA.json` produced by `aidd-ops`.

```bash
python ecossistema.py open-motor --plano <PLANO-INFRAESTRUTURA.json> --pasta <destination> [--sem-llm]
```

Old name `factory` (and `/factory`) still works for one cycle and prints an "old name" warning (table in `componentes/compartilhado/specs/NOMES-ANTIGOS.json`).
Done when: the command exits 0 and `FACTORY_OUTPUT.json` exists in the destination.
Architecture: `docs/features/v2_arquitetura-aidd-ops-factory.md`.
