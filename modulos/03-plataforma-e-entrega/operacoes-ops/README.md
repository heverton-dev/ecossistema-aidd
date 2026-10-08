# Fatia — Operações Ops

Infraestrutura self-hosted a partir de requisitos em linguagem natural: intake, curadoria, sizing, hardening e deploy.

## Responsabilidades
- Geração de Dockerfile, docker-compose e deploy a partir de peças do catálogo (`aidd-ops`).
- Hardening idempotente de VPS e cofre de segredos (sops + age).
- Interface pública da fatia: `interface.py`.

Ferramenta: [`aidd-ops`](aidd-ops/README.md). Regras para agentes: [AGENTS.md](AGENTS.md).
