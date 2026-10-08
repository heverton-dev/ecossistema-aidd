# aidd-enterprise

Blindagem de projetos: injeta componentes de missão crítica com selo SHA-256 e impõe Clean Architecture por gates rígidos.

## Uso rápido

```bash
python ecossistema.py enterprise inject skill <nome>
```

- Guia completo (instalação, arquitetura, testes): [GUIA.md](GUIA.md)
- Regras e invariantes para agentes: [AGENTS.md](AGENTS.md)

## Fronteiras Canônicas e Responsabilidades

Conforme o mapa oficial de arquitetura (`MAPA-DONOS-FERRAMENTAS.json` e `G_FRONTEIRA_FERRAMENTAS.py`):

- **Responsabilidades:**
  - `blindagem_componentes_missao_critica`
  - `auditoria_integridade_sha256_e_selo`
  - `verificacao_drift_nucleo_compartilhado`
- **Pode guardar peças do catálogo:** Não (`pode_guardar_pecas: false`).
- **Dono do conteúdo de:** `receita_injetor`, `catalogo_blindagem_sha256`, `regras_missao_critica`.
- **Pode conter:** `src/**`, `scripts/**`, `schemas/**`, `tests/**`, `templates/rules/**`.
- **Nunca conter (violações de fronteira):**
  - `**/Dockerfile*`
  - `**/docker-compose*`
  - `**/deploy.sh`
  - `**/nginx/**`
  - `**/mcp_server*`
  - `**/webhook*`
  - `**/openapi*`
- **Zona de escrita no projeto:** `COMPONENT-REGISTRY.json`, `RELATORIO-AUDITORIA.json`, `templates/rules/**`, `.aidd/selo/**`, `HANDOFF_ENTERPRISE_OPS.json`.
