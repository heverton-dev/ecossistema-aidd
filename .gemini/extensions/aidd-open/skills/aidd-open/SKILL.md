---
name: aidd-open
description: Runs Triad Flow 02 (open-source engines) end to end - curates tested open-source engines, integrates them as VSA slices through the aidd-open engine, then master, enterprise and ops; also runs only the engine that generates a multi-service stack from a PLANO-INFRAESTRUTURA.json. Use when the user wants an app built on open-source engines or a deployable stack from an infrastructure plan, or types "/open", "/aidd-open", "open", "open-motor", "/factory", "factory", "criar com open-source", "integrar motor open source", "gerar stack", "gerar gateway", "gerar compose".
---

# aidd-open (Flow 02, open-source engines)

Pipeline: `[FORGE -> PLANNER -> MASTER -> DISPATCH] -> {ENGINE nas Worktrees} -> [BARREIRA (Rebase Sync) -> ENTERPRISE -> OPS -> 54 GATES]`

| Stage | Tool | Output |
|---|---|---|
| 1. Fundação | `aidd-forge` | blindagem agentica e hooks git |
| 2. Planejamento | `aidd-planner` | contratos BDD/SDD, integrações e requisitos |
| 3. Fatiamento VSA | `aidd-master` | fatiamento vertical e contratos de fatias |
| 4. Despacho & Worktrees | `aidd-dispatch` | isolamento em git worktrees com micro-gates |
| 5. Motor | `aidd-open` (`modulos/02-triade-motores/fluxo-02-open/core/aidd-open`) | integração curada de motores open source |
| 6. Barreira & Rebase | `aidd-master` | rebase determinístico e merge das fatias |
| 7. Blindagem | `aidd-enterprise` | auditoria SHA-256 e gateways corporativos |
| 8. Infraestrutura | `aidd-ops` | Dockerfile, compose e redes isoladas |
| 9. Qualidade Global | `54 Gates` | auditoria determinística final |

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

## Negative Guardrails

- NEVER configure an LLM API key to run the engine phases: the running harness is the model; for a no-model run use `open-motor ... --sem-llm`.
- NEVER call `open-motor` without a `PLANO-INFRAESTRUTURA.json` produced by `aidd-ops`; do not hand-craft one to skip that stage.
- NEVER treat `open ... --dry-run` exit 0 as delivery: dry-run skips every command and does not check contracts C1-C5.
- NEVER write real secrets into the generated per-service `.env` files or `docker-compose`; keep placeholders and tell the user which keys to fill.
- NEVER type `/open` inside Antigravity CLI (`agy`): it opens files there; use `/aidd-open`.
- NEVER mark Flow 02 done while `FACTORY_OUTPUT.json` has `resumo.erros` above 0 (an artifact with `status: erro`, e.g. the cross-service validation).

## Failure Modes & Fallback

- **Stage stops with "não gravou HANDOFF_ENGINE_MASTER.json":** the engine did not finish; rerun `python ecossistema.py open-motor --plano <PLANO-INFRAESTRUTURA.json> --pasta <dest>` alone, read its error, then restart `open`.
- **Engine phase blocks waiting for a model answer:** answer the delegated request in `<dest>/.aidd/cache/`, or rerun with `--sem-llm` if the user accepts a deterministic stack.
- **Chosen open-source engine has no tested image or license fit:** stop and ask the user for an alternative engine; do not vendor an untested one.

## Stopping Checklist

- [ ] `python ecossistema.py open --nome "<Name>" --slug <slug> --dominio <domain> --pasta <dest> > open.log 2>&1; echo $? > open.rc` and `open.rc` holds `0`.
- [ ] `<dest>/ORQUESTRACAO_EXECUCAO.json` exists and `<dest>/FACTORY_OUTPUT.json` has `resumo.erros` equal to `0`.
- [ ] `docker compose -f <dest>/docker-compose.yml config > dc.log 2>&1; echo $? > dc.rc` holds `0`.
- [ ] `python modulos/03-plataforma-e-entrega/gates/G_QUARTETO_SINE_QUA_NON.py --target <dest> > q-open.log 2>&1; echo $? > q-open.rc` holds `0` (the four routes are served by the FastAPI gateway).
