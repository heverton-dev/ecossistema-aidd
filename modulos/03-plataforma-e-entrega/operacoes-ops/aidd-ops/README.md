# aidd-ops

Meta-orquestrador de infraestrutura: recebe requisitos em linguagem natural e provisiona stacks open source self-hosted (intake, curadoria, sizing, hardening e deploy).

## Uso rápido

```bash
python ecossistema.py ops "<texto>" --pasta <dest>
```

- Guia completo (instalação, arquitetura, testes): [GUIA.md](GUIA.md)
- Regras e invariantes para agentes: [AGENTS.md](AGENTS.md)

## Fronteiras Canônicas e Responsabilidades

Conforme o mapa oficial de arquitetura (`MAPA-DONOS-FERRAMENTAS.json` e `G_FRONTEIRA_FERRAMENTAS.py`):

- **Responsabilidades:**
  - `geracao_infraestrutura_docker_compose`
  - `provisionamento_vps_e_hardening`
  - `gerenciamento_secrets_sops_age`
  - `monitoramento_uptime_e_deploy`
- **Pode guardar peças do catálogo:** Não (`pode_guardar_pecas: false`).
- **Dono do conteúdo de:** `receitas_infra`, `templates_dockerfile_compose`, `scripts_deploy_nginx`.
- **Pode conter:** `src/**`, `scripts/**`, `schemas/**`, `tests/**`, `templates/infra/**`.
- **Nunca conter (violações de fronteira):**
  - `**/src/modules/**`
  - `**/src/core/**`
  - `**/mcp_server*`
  - `**/G_*.py`
  - `**/vsa_generator*`
- **Zona de escrita no projeto:** `Dockerfile`, `docker-compose.yml`, `deploy.sh`, `nginx/**`, `.sops.yaml`, `secrets/**`, `monitoramento/**`.
