# aidd-pure

Fluxo 01 da Tríade: motor de 8 fases que leva uma ideia em linguagem natural a um projeto testado (schemas, scripts, testes e documentação), com TDD Red-Green estrito.

## Uso rápido

```bash
python ecossistema.py pure-motor "Minha ideia"
```

- Guia completo (instalação, arquitetura, testes): [GUIA.md](GUIA.md)
- Regras e invariantes para agentes: [AGENTS.md](AGENTS.md)

## Fronteiras Canônicas e Responsabilidades

Conforme o mapa oficial de arquitetura (`MAPA-DONOS-FERRAMENTAS.json` e `G_FRONTEIRA_FERRAMENTAS.py`):

- **Responsabilidades:**
  - `construcao_do_zero_tdd_red_green`
  - `geracao_fatias_dominio_vsa_zero`
- **Pode guardar peças do catálogo:** Não (`pode_guardar_pecas: false`).
- **Dono do conteúdo de:** `fatias_dominio_pure`, `testes_unitarios_dominio_pure`.
- **Pode conter:** `src/**`, `scripts/**`, `schemas/**`, `tests/**`, `templates/dominio/**`.
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
- **Zona de escrita no projeto:** `src/modules/*/**`, `frontend/app/*/**`, `HANDOFF_ENGINE_MASTER.json`, `.aidd/cache/**`.

---
