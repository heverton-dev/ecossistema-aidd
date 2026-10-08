# aidd-master

Fatiamento modular: monólito modular em fatias verticais (VSA) com Clean Architecture e gates anti-atalho.

## Uso rápido

```bash
python ecossistema.py master add-module <nome>
```

- Guia completo (instalação, arquitetura, testes): [GUIA.md](GUIA.md)
- Regras e invariantes para agentes: [AGENTS.md](AGENTS.md)

## Fronteiras Canônicas e Responsabilidades

Conforme o mapa oficial de arquitetura (`MAPA-DONOS-FERRAMENTAS.json` e `G_FRONTEIRA_FERRAMENTAS.py`):

- **Responsabilidades:**
  - `harmonizacao_monolito_modular_vsa`
  - `despacho_topologico_worktrees_dispatch`
  - `implementacao_quarteto_sine_qua_non`
  - `casca_compartilhada_frontend_backend`
- **Pode guardar peças do catálogo:** Não (`pode_guardar_pecas: false`).
- **Dono do conteúdo de:** `receitas_quarteto`, `nucleo_src_core`, `rotas_quarteto`.
- **Pode conter:** `src/**`, `scripts/**`, `schemas/**`, `tests/**`, `templates/quarteto/**`.
- **Nunca conter (violações de fronteira):**
  - `**/Dockerfile*`
  - `**/docker-compose*`
  - `**/deploy.sh`
  - `**/nginx/**`
  - `**/.sops.yaml`
  - `**/secrets/**`
  - `**/G_*.py`
- **Zona de escrita no projeto:** `src/core/**`, `src/server.py`, `src/shared/**`, `frontend/**`, `docs/**`, `HANDOFF_MASTER_ENTERPRISE.json`.
