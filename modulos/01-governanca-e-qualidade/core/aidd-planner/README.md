# aidd-planner

Motor de planejamento da Tríade: transforma o pedido em PLANNER.json validado por schema, combustível dos fluxos pure (01), open (02) e freedom (03).

## Uso rápido

```bash
python ecossistema.py planner init|validate|export|audit
```

- Guia completo (instalação, arquitetura, testes): [GUIA.md](GUIA.md)
- Regras e invariantes para agentes: [AGENTS.md](AGENTS.md)

## Fronteiras Canônicas e Responsabilidades

Conforme o mapa oficial de arquitetura (`MAPA-DONOS-FERRAMENTAS.json` e `G_FRONTEIRA_FERRAMENTAS.py`):

- **Responsabilidades:**
  - `desenho_planta_baixa_arquitetural`
  - `intake_sdd_bdd_e_especificacao`
  - `roteamento_tickets_para_ferramentas`
  - `calculo_dinamico_perfil_app`
- **Pode guardar peças do catálogo:** Não (`pode_guardar_pecas: false`).
- **Dono do conteúdo de:** `planta_arquitetura`, `tickets_roteados`, `perfil_app_dinamico`.
- **Pode conter:** `src/**`, `scripts/**`, `schemas/**`, `tests/**`, `templates/plano/**`.
- **Nunca conter (violações de fronteira):**
  - `**/Dockerfile*`
  - `**/docker-compose*`
  - `**/deploy.sh`
  - `**/nginx/**`
  - `**/mcp_server*`
  - `**/webhook*`
  - `**/openapi*`
  - `**/swagger*`
  - `**/G_*.py`
  - `**/*inject*`
- **Zona de escrita no projeto:** `PLANNER.json`, `HANDOFF_PLANNER_ENGINE.json`, `VSA_DISPATCH.json`, `DESIGN-SYSTEM.json`.
