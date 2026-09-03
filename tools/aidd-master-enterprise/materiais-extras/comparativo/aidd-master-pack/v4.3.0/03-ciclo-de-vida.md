# Ciclo de Vida Completo de Uso — AIDD Master Pack `v4.3.0`

> **Tag analisada:** `v4.3.0`
> Todas as fases abaixo foram reconstruídas a partir do comportamento real de `scripts/aidd.py`, `scripts/compose_suite.py`, `scripts/add_module.py`, `scripts/provision_project.py`, `scripts/gates/*`, `scripts/test_live.py` e `src/server.py` extraídos do snapshot da tag.

---

## Visão Geral do Ciclo

```
┌───────────────────────────────────────────────────────────────────────────┐
│ FASE 0: OBTENÇÃO DO PACOTE                                                │
│ git clone / instalação como skill em ~/.agents/skills/aidd-master-pack   │
└──────────────────────────────────────┬────────────────────────────────────┘
                                       ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ FASE 1: COMPOSIÇÃO OU PROVISIONAMENTO DA SUÍTE                            │
│ python scripts/compose_suite.py <destino> <nome> [dominios...]           │
│   -> cria estrutura de pastas e copia o Shared Kernel (core + UI)        │
│ (alternativa legada: scripts/provision_project.py "descrição")           │
└──────────────────────────────────────┬────────────────────────────────────┘
                                       ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ FASE 2: GERAÇÃO ATÔMICA DE MÓDULOS (FATIAS VERTICAIS)                     │
│ python scripts/add_module.py <nome_modulo> [descricao]                   │
│   -> gera models.py, services.py (listar/criar/deletar), routes.py,      │
│      componente HTML e teste unitário — um comando por módulo            │
└──────────────────────────────────────┬────────────────────────────────────┘
                                       ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ FASE 3: VALIDAÇÃO MECÂNICA (GATES DETERMINÍSTICOS)                        │
│ python scripts/aidd.py audit                                              │
│   -> executa em sequência: G_SEGREDOS, G_QUALIDADE, G_HARNESS_COMPAT      │
│ (opcional, manual) python scripts/gates/G_SEGURANCA.py                    │
│   -> auditoria de 7 camadas (OWASP, JWT, SQLi, Nginx, Docker, WAL, API)   │
└──────────────────────────────────────┬────────────────────────────────────┘
                                       ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ FASE 4: TESTES (UNITÁRIOS E DE CARGA)                                     │
│ python scripts/aidd.py test unit   -> pytest -v                          │
│ python scripts/aidd.py test load   -> locust headless 5s                 │
└──────────────────────────────────────┬────────────────────────────────────┘
                                       ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ FASE 5: EXECUÇÃO DO SERVIDOR (OUTPUT OPERACIONAL)                         │
│ python src/server.py                                                      │
│   -> socketserver.ThreadingTCPServer na porta 3000 (multi-thread)        │
│   -> Portais: /, /docs, /docs/guia, /mcp, /webhooks, /openapi.json       │
└──────────────────────────────────────┬────────────────────────────────────┘
                                       ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ FASE 6: VERIFICAÇÃO DE PRODUÇÃO/HOMOLOGAÇÃO (NOVO NESTA TAG)              │
│ python scripts/test_live.py                                               │
│   -> bate nos 8 endpoints, testa login JWT e simulador de webhook HMAC   │
└──────────────────────────────────────┬────────────────────────────────────┘
                                       ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ FASE 7: DEPLOY                                                            │
│ python scripts/aidd.py deploy docker  -> docker compose up -d --build    │
│ python scripts/aidd.py deploy vps     -> orienta a rodar deploy.sh na VPS│
└──────────────────────────────────────┬────────────────────────────────────┘
                                       ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ FASE 8: INSPEÇÃO DE STATUS (OPCIONAL, A QUALQUER MOMENTO)                 │
│ python scripts/aidd.py status                                             │
│   -> lê PLANO-EXECUCAO-ESTRUTURADO.json (se existir) e lista módulos     │
│      ativos em src/modules/                                              │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Detalhamento por Fase

### Fase 0 — Obtenção do pacote
O pacote é distribuído como repositório Git (`README.md`, `SKILL.md`, `LICENSE` na raiz) e também é referenciado como *skill* instalável em `~/.agents/skills/aidd-master-pack/` — é para lá que `provision_project.py` e `provision`-style scripts esperam encontrar `templates/v2` e `templates/gates` na hora de copiar arquivos para um novo projeto.

### Fase 1 — Composição/provisionamento
Existem dois caminhos distintos e não totalmente integrados nesta tag:
- **`compose_suite.py <target_dir> <suite_name> [modulos...]`** (caminho documentado no `SKILL.md`): cria `src/core`, `src/shared/ui`, `src/static`, `src/modules`, `tests`, e copia os 5 arquivos do *shared kernel* (`database.py`, `events.py`, `webhooks.py`, `security.py`, `openapi.py`) e os componentes de feedback de UI. Ele **não** gera os módulos de domínio em si — apenas prepara o esqueleto.
- **`provision_project.py <descrição>`** (caminho legado "v2.0"): cria a estrutura em um diretório fixo do Windows (`C:\Users\trcnologia\orca\workspaces\PROJETOS Criados com IA\proj_<slug>`), copia o *shared kernel*, os scripts (`aidd.py`, `add_module.py`) e os gates a partir do hub de skills instalado localmente, e roda `git init`.

### Fase 2 — Geração atômica de módulos
`add_module.py <nome> [descricao]` é chamado **uma vez por domínio de negócio** (ex.: `faturamento`, `frotas`, `wms`). Cada execução cria, dentro de `src/modules/<slug>/`:
- `models.py` — schema SQLite (`CREATE TABLE IF NOT EXISTS mod_<slug> (...)`, índice em `ativo`).
- `services.py` — classe `<Slug>Service` com `listar()`, `criar()`, `deletar()` (emitindo eventos via `EventBus`).
- `routes.py` — registra `GET /api/<slug>`, `POST /api/<slug>` e `POST /api/<slug>/deletar` no `RouteRegistry`.
- Um componente visual (`src/static/components/<slug>.html`) com card, lista e formulário de criação.
- Um teste unitário (`tests/unit/test_<slug>.py`) cobrindo criar → listar → deletar.

### Fase 3 — Validação mecânica (gates)
`aidd.py audit` executa, em ordem, `G_SEGREDOS.py` (varredura de segredos com regex + entropia de Shannon), `G_QUALIDADE.py` (`py_compile` em todos os `.py`) e `G_HARNESS_COMPAT.py` (checagem simbólica, sempre aprova). Qualquer falha interrompe a cadeia com `exit 1`. O quarto gate desta geração, `G_SEGURANCA.py` — introduzido na tag anterior e reforçado nesta — **não está incluído** nessa cadeia automática; é executado manualmente e produz um relatório de 7 camadas com nota percentual de "blindagem".

### Fase 4 — Testes
`aidd.py test unit` roda `pytest -v` na raiz do projeto gerado. `aidd.py test load` roda um teste de carga headless com Locust por 5 segundos contra `http://localhost:3000` (requer o servidor já rodando e o arquivo `tests/load/locustfile.py`, copiado do *shared kernel*).

### Fase 5 — Execução do servidor
`python src/server.py` inicializa `Database`, `EventBus`, `WebhookDispatcher`, `RouteRegistry` e o `LogisticaMCPServer` (ou equivalente por domínio), cria as tabelas via `init_all_schemas`, e sobe um `socketserver.ThreadingTCPServer` multi-thread na porta 3000, publicando os portais: aplicação (`/`), Swagger Studio (`/docs`), guia de arquitetura (`/docs/guia`), portal MCP (`/mcp` + JSON-RPC em `/api/mcp/rpc`) e Webhook Studio (`/webhooks`).

### Fase 6 — Verificação de produção/homologação (novidade desta tag)
`scripts/test_live.py` é o script de "teste de fogo" adicionado na v4.3.0: ele confirma que os 5 portais respondem HTTP 200, que o login JWT (`POST /api/auth/login`) devolve um token válido, e que o simulador de webhook (`POST /api/webhooks/testar`) devolve uma assinatura HMAC — validando de ponta a ponta que a instância local está pronta para ser chamada de "homologada".

### Fase 7 — Deploy
`aidd.py deploy docker` chama `docker compose up -d --build` usando o `Dockerfile` (usuário não-root, `HEALTHCHECK` nativo) e o `docker-compose.yml` do *shared kernel*. `aidd.py deploy vps` apenas instrui o usuário a rodar `deploy.sh` manualmente no servidor — não executa deploy remoto por si.

### Fase 8 — Status
`aidd.py status` é o único ponto do pacote que **lê** `PLANO-EXECUCAO-ESTRUTURADO.json` (se o arquivo existir no diretório do projeto) para reportar nome, versão e status do projeto, além de listar os módulos ativos encontrados em `src/modules/`. Nenhum script desta tag **gera** esse arquivo — ver `plano-de-execucao.md` para detalhes.

## Saída final entregue ao usuário
Ao final do ciclo, o "output" é uma aplicação Python autocontida rodando localmente na porta 3000 (ou publicada via Docker/VPS), com banco SQLite WAL persistido em disco, documentação OpenAPI/Swagger viva, painel de configuração de Webhooks, portal MCP para conexão com agentes de IA, e um relatório de gates (sintaxe, segredos, harness e, se rodado manualmente, segurança) confirmando o estado de qualidade do código gerado.
