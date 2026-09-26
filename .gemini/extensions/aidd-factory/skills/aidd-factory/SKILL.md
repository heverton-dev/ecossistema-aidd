---
name: aidd-factory
description: Generates a complete multi-service application stack (gateway, frontend, compose, webhooks, docs) from a PLANO-INFRAESTRUTURA.json produced by aidd-ops. Use when the user wants to go from an infrastructure plan to a deployable app, or says "factory", "/factory", "gerar stack", "gerar gateway", "gerar frontend", "gerar compose".
---

# aidd-factory

## Run

```bash
python ecossistema.py factory --plano <PLANO-INFRAESTRUTURA.json> --pasta <destination> [--sem-llm]
```

Done when: the command exits 0 and `FACTORY_OUTPUT.json` exists in the destination.

## Pipeline phases

| Phase | Output | Method |
|---|---|---|
| 1 | Plan analysis | Deterministic |
| 2 | FastAPI gateway | Jinja2 templates |
| 3 | Next.js whitelabel frontend | Jinja2 templates |
| 4 | Unified docker-compose | Deterministic |
| 5 | init-multiple-databases.sh | Deterministic |
| 6 | .env per service | Deterministic |
| 7 | Webhooks/integrations | Templates |
| 8 | Swagger/OpenAPI | Deterministic |
| 9 | Cross-service validation | Deterministic |

## Artifacts

`docker-compose.yml`, `init-multiple-databases.sh`, `.env.*`, `src/gateway/` (FastAPI), `frontend/` (Next.js + Tailwind), `openapi.json`, `README.md`, `FACTORY_OUTPUT.json`.

## References

- Architecture: `docs/features/v2_arquitetura-aidd-ops-factory.md`
- Improvement report: `docs/melhorias/14-09-2026_melhoria-aidd-factory-implementacao.json`
