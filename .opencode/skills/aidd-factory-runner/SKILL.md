---
name: aidd-factory-runner
description: Application code and integration generator for multi-service stacks.
---

# AIDD-Factory Runner

Use this skill when the user wants to generate a complete application stack (gateway, frontend, docker, docs, webhooks) from a PLANO-INFRAESTRUTURA.json produced by aidd-ops. Trigger on mentions of 'factory', 'generate stack', 'generate gateway', 'generate frontend', 'generate compose', 'factory pipeline', or when the user wants to go from infrastructure plan to deployable application.

## Usage

```bash
python ecossistema.py factory --plano <PLANO-INFRAESTRUTURA.json> --pasta <destino> [--sem-llm]
```

## Pipeline Phases

| Phase | Description | Method |
|-------|-------------|--------|
| 1 | Plan analyzer | Deterministic |
| 2 | FastAPI gateway | Jinja2 templates |
| 3 | Next.js whitelabel frontend | Jinja2 templates |
| 4 | Unified docker-compose | Deterministic |
| 5 | init-multiple-databases.sh | Deterministic |
| 6 | .env per service | Deterministic |
| 7 | Webhooks/integrations | Templates |
| 8 | Swagger/OpenAPI | Deterministic |
| 9 | Cross-service validation | Deterministic |

## Generated Artifacts

- `docker-compose.yml` unified
- `init-multiple-databases.sh`
- `.env.*` per service
- `src/gateway/` (FastAPI)
- `frontend/` (Next.js + Tailwind)
- `openapi.json` + `README.md`
- `FACTORY_OUTPUT.json`

## References
- Architecture doc: `docs/features/v2_arquitetura-aidd-ops-factory.md`
- Improvement report: `docs/melhorias/14-09-2026_melhoria-aidd-factory-implementacao.json`
