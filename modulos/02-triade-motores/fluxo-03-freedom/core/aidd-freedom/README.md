# aidd-freedom

Fluxo 03 da Tríade: tira apps de plataformas low-code (Lovable, v0, Bolt) do aprisionamento, converte Supabase em PostgreSQL puro e empacota para VPS própria.

## Uso rápido

```bash
python ecossistema.py freedom-motor scan|convert-db|merge|pack
```

- Guia completo (instalação, arquitetura, testes): [GUIA.md](GUIA.md)
- Regras e invariantes para agentes: [AGENTS.md](AGENTS.md)

## Fronteiras Canônicas e Responsabilidades

Conforme o mapa oficial de arquitetura (`MAPA-DONOS-FERRAMENTAS.json` e `G_FRONTEIRA_FERRAMENTAS.py`):

- **Responsabilidades:**
  - `desacoplamento_vendor_lockin_lowcode`
  - `migracao_banco_supabase_para_postgres`
  - `preservacao_ui_e_extracao_fatias_bridge`
- **Pode guardar peças do catálogo:** Não (`pode_guardar_pecas: false`).
- **Dono do conteúdo de:** `fatias_dominio_freedom`, `scripts_migracao_sql_freedom`.
- **Pode conter:** `src/**`, `scripts/**`, `schemas/**`, `tests/**`, `parsers/**`.
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
- **Zona de escrita no projeto:** `.aidd/bridge-manifest.json`, `src/modules/*/**`, `frontend/app/*/**`, `HANDOFF_ENGINE_MASTER.json`, `.aidd/cache/**`.
