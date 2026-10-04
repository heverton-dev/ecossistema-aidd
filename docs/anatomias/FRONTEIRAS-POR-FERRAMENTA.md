# Fronteiras Canônicas por Ferramenta — Ecossistema AIDD

> Fonte única da verdade para delimitação de escopo, posse de código e fronteiras das 8 ferramentas.
> Derivado diretamente de `componentes/compartilhado/specs/MAPA-DONOS-FERRAMENTAS.json` e verificado pelo gate `G_FRONTEIRA_FERRAMENTAS.py` (Ciclo 01).

---

## 1. Visão Geral da Matriz de Fronteiras

| Ferramenta | Etapa Canônica | Papel Central | Pode Guardar Peças? |
|---|---|---|---|
| `aidd-forge` | Etapa 1 | Preparação do terreno, governança global e almoxarifado | **Sim (Único)** |
| `aidd-planner` | Etapa 2 | Desenho de planta baixa, especificação e roteamento de tickets | Não |
| `aidd-pure` | Etapa 3 (Fluxo 01) | Construção do zero via TDD Red/Green e fatias VSA | Não |
| `aidd-open` | Etapa 3 (Fluxo 02) | Integração e curadoria de motores open-source | Não |
| `aidd-freedom` | Etapa 3 (Fluxo 03) | Desacoplamento de vendor lock-in low-code para VPS | Não |
| `aidd-master` | Etapa 4 | Integração monólito modular VSA, casca e rotas do Quarteto | Não |
| `aidd-enterprise` | Etapa 5 | Blindagem missão crítica, selo SHA-256 e auditoria | Não |
| `aidd-ops` | Etapa 6 | Geração de infraestrutura, Docker Compose, VPS e segredos | Não |

---

## 2. Detalhamento por Ferramenta

### `aidd-forge`
- **Responsabilidades:**
  - `preparo_terreno_e_prontidao_projeto`
  - `guarda_e_distribuicao_almoxarifado_pecas`
  - `instalacao_e_auditoria_leis_guardas`
  - `governanca_harnesses_e_regras_globais`
- **Pode guardar peças do catálogo:** `true`
- **Dono do conteúdo de:** `gates_projeto`, `catalogo_almoxarifado`, `regras_harness`, `governance_kit`
- **Pode conter:** `src/**`, `scripts/**`, `schemas/**`, `tests/**`, `templates/**`, `gates/**`, `almoxarifado/**`
- **Nunca conter (Proibido):**
  - `**/vsa_generator*`
  - `**/dispatch_pipeline*`
  - `**/docker-compose*`
- **Zona de escrita no projeto:** `.git/hooks/**`, `gates/**`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.aidd/**`, `.aidd/HANDOFF_FORGE_PLANNER.json`

---

### `aidd-planner`
- **Responsabilidades:**
  - `desenho_planta_baixa_arquitetural`
  - `intake_sdd_bdd_e_especificacao`
  - `roteamento_tickets_para_ferramentas`
  - `calculo_dinamico_perfil_app`
- **Pode guardar peças do catálogo:** `false`
- **Dono do conteúdo de:** `planta_arquitetura`, `tickets_roteados`, `perfil_app_dinamico`
- **Pode conter:** `src/**`, `scripts/**`, `schemas/**`, `tests/**`, `templates/plano/**`
- **Nunca conter (Proibido):**
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
- **Zona de escrita no projeto:** `PLANNER.json`, `HANDOFF_PLANNER_ENGINE.json`, `VSA_DISPATCH.json`, `DESIGN-SYSTEM.json`

---

### `aidd-pure`
- **Responsabilidades:**
  - `construcao_do_zero_tdd_red_green`
  - `geracao_fatias_dominio_vsa_zero`
- **Pode guardar peças do catálogo:** `false`
- **Dono do conteúdo de:** `fatias_dominio_pure`, `testes_unitarios_dominio_pure`
- **Pode conter:** `src/**`, `scripts/**`, `schemas/**`, `tests/**`, `templates/dominio/**`
- **Nunca conter (Proibido):**
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
- **Zona de escrita no projeto:** `src/modules/*/**`, `frontend/app/*/**`, `HANDOFF_ENGINE_MASTER.json`, `.aidd/cache/**`

---

### `aidd-open`
- **Responsabilidades:**
  - `curadoria_motores_opensource`
  - `integracao_fatias_dominio_factory`
- **Pode guardar peças do catálogo:** `false`
- **Dono do conteúdo de:** `fatias_dominio_open`, `adaptadores_motores_opensource`
- **Pode conter:** `src/**`, `scripts/**`, `schemas/**`, `tests/**`, `templates/dominio/**`
- **Nunca conter (Proibido):**
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
- **Zona de escrita no projeto:** `src/modules/*/**`, `frontend/app/*/**`, `HANDOFF_ENGINE_MASTER.json`, `.aidd/cache/**`

---

### `aidd-freedom`
- **Responsabilidades:**
  - `desacoplamento_vendor_lockin_lowcode`
  - `migracao_banco_supabase_para_postgres`
  - `preservacao_ui_e_extracao_fatias_bridge`
- **Pode guardar peças do catálogo:** `false`
- **Dono do conteúdo de:** `fatias_dominio_freedom`, `scripts_migracao_sql_freedom`
- **Pode conter:** `src/**`, `scripts/**`, `schemas/**`, `tests/**`, `parsers/**`
- **Nunca conter (Proibido):**
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
- **Zona de escrita no projeto:** `.aidd/bridge-manifest.json`, `src/modules/*/**`, `frontend/app/*/**`, `HANDOFF_ENGINE_MASTER.json`, `.aidd/cache/**`

---

### `aidd-master`
- **Responsabilidades:**
  - `harmonizacao_monolito_modular_vsa`
  - `despacho_topologico_worktrees_dispatch`
  - `implementacao_quarteto_sine_qua_non`
  - `casca_compartilhada_frontend_backend`
- **Pode guardar peças do catálogo:** `false`
- **Dono do conteúdo de:** `receitas_quarteto`, `nucleo_src_core`, `rotas_quarteto`
- **Pode conter:** `src/**`, `scripts/**`, `schemas/**`, `tests/**`, `templates/quarteto/**`
- **Nunca conter (Proibido):**
  - `**/Dockerfile*`
  - `**/docker-compose*`
  - `**/deploy.sh`
  - `**/nginx/**`
  - `**/.sops.yaml`
  - `**/secrets/**`
  - `**/G_*.py`
- **Zona de escrita no projeto:** `src/core/**`, `src/server.py`, `src/shared/**`, `frontend/**`, `docs/**`, `HANDOFF_MASTER_ENTERPRISE.json`

---

### `aidd-enterprise`
- **Responsabilidades:**
  - `blindagem_componentes_missao_critica`
  - `auditoria_integridade_sha256_e_selo`
  - `verificacao_drift_nucleo_compartilhado`
- **Pode guardar peças do catálogo:** `false`
- **Dono do conteúdo de:** `receita_injetor`, `catalogo_blindagem_sha256`, `regras_missao_critica`
- **Pode conter:** `src/**`, `scripts/**`, `schemas/**`, `tests/**`, `templates/rules/**`
- **Nunca conter (Proibido):**
  - `**/Dockerfile*`
  - `**/docker-compose*`
  - `**/deploy.sh`
  - `**/nginx/**`
  - `**/mcp_server*`
  - `**/webhook*`
  - `**/openapi*`
- **Zona de escrita no projeto:** `COMPONENT-REGISTRY.json`, `RELATORIO-AUDITORIA.json`, `templates/rules/**`, `.aidd/selo/**`, `HANDOFF_ENTERPRISE_OPS.json`

---

### `aidd-ops`
- **Responsabilidades:**
  - `geracao_infraestrutura_docker_compose`
  - `provisionamento_vps_e_hardening`
  - `gerenciamento_secrets_sops_age`
  - `monitoramento_uptime_e_deploy`
- **Pode guardar peças do catálogo:** `false`
- **Dono do conteúdo de:** `receitas_infra`, `templates_dockerfile_compose`, `scripts_deploy_nginx`
- **Pode conter:** `src/**`, `scripts/**`, `schemas/**`, `tests/**`, `templates/infra/**`
- **Nunca conter (Proibido):**
  - `**/src/modules/**`
  - `**/src/core/**`
  - `**/mcp_server*`
  - `**/G_*.py`
  - `**/vsa_generator*`
- **Zona de escrita no projeto:** `Dockerfile`, `docker-compose.yml`, `deploy.sh`, `nginx/**`, `.sops.yaml`, `secrets/**`, `monitoramento/**`
