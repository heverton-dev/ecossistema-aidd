# Ciclo de Vida Completo de Uso — AIDD Master Pack v4.0.1

> **Tag analisada:** `v4.0.1`.
> Este documento descreve o ciclo de vida real de uso do pacote nesta tag, com base exclusivamente no comportamento observável de `scripts/aidd.py`, `scripts/provision_project.py`, `scripts/add_module.py` e `templates/gates/*.py`.

---

## 1. Visão Geral do Ciclo

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ FASE 0: OBTENÇÃO DO PACOTE                                                  │
│ git clone / cópia da pasta aidd-master-pack-v4 para ~/.agents/skills/       │
│ Nenhum instalador, nenhuma dependência de terceiros a instalar              │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ FASE 1: PROVISIONAMENTO DE UM NOVO PROJETO                                  │
│ $ python scripts/provision_project.py "nome do projeto"                     │
│ (ou via CLI: $ python scripts/aidd.py init "nome do projeto")               │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ FASE 2: GERAÇÃO DE MÓDULOS VERTICAIS (REPETÍVEL)                            │
│ $ python scripts/aidd.py add-module <nome> [--descricao "..."]              │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ FASE 3: TESTES                                                              │
│ $ python scripts/aidd.py test [unit|load|e2e|all]                           │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ FASE 4: AUDITORIA MECÂNICA (GATES)                                          │
│ $ python scripts/aidd.py audit                                              │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ FASE 5: DEPLOY                                                              │
│ $ python scripts/aidd.py deploy [docker|vps|vercel]                         │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ FASE 6: INSPEÇÃO DE STATUS (OPCIONAL, A QUALQUER MOMENTO)                   │
│ $ python scripts/aidd.py status                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Detalhamento de Cada Fase

### FASE 0 — Obtenção do Pacote

O pacote não possui instalador nem `setup.py`/`pyproject.toml`. É consumido como uma **skill agêntica** (ver `SKILL.md`), copiado ou clonado para o diretório de skills do agente (`~/.agents/skills/aidd-master-pack/` na convenção usada pelo próprio `provision_project.py`). Não há passo de "build" — os scripts Python rodam diretamente com a stdlib.

### FASE 1 — Provisionamento (`provision_project.py` / `aidd.py init`)

A função `provision(project_desc, base_dir=...)`:
1. Faz o *slug* dos 3 primeiras palavras da descrição do projeto (ex.: "Catálogo Digital e Loja" → `catalogo-digital-e`).
2. Cria a árvore de diretórios: `src/core`, `src/shared`, `src/modules`, `src/static/components`, `tests/unit`, `tests/load`, `scripts/gates`.
3. Copia o **Shared Kernel v2** (`database.py`, `events.py`, `openapi.py`, `webhooks.py`, pasta `shared/`) do hub de templates para dentro do projeto novo.
4. Copia `Dockerfile`, `docker-compose.yml`, `deploy.sh` e `locustfile.py` (teste de carga) do hub.
5. Copia `aidd.py` e `add_module.py` para `scripts/` do projeto.
6. Copia os 3 gates (`G_SEGREDOS.py`, `G_QUALIDADE.py`, `G_HARNESS_COMPAT.py`) para `scripts/gates/`.
7. Roda `git init` no diretório do novo projeto, se ainda não for um repositório Git.

**Observação:** o `base_dir` padrão é um caminho absoluto do Windows (`C:\Users\trcnologia\orca\workspaces\PROJETOS Criados com IA`) — em outra máquina, é necessário passar um `base_dir` customizado ou editar o script.

### FASE 2 — Geração de Módulos Verticais (`add_module.py` / `aidd.py add-module`)

Para cada módulo (`criar_modulo(nome_modulo, descricao)`), o script gera atomicamente 5 artefatos dentro de `src/modules/<slug>/`:
1. `models.py` — cria tabela SQLite `mod_<slug>` (id, titulo, dados_json, ativo, criado_em) com índice em `ativo`.
2. `services.py` — classe `<Slug>Service` com `listar()`, `criar()`, `deletar()`, emitindo eventos no `EventBus` (`<slug>_criado`, `<slug>_deletado`).
3. `routes.py` — registra 3 rotas REST (`GET /api/<slug>`, `POST /api/<slug>`, `POST /api/<slug>/deletar`) via `RouteRegistry` do `core/openapi.py`.
4. Um componente visual HTML em `src/static/components/<slug>.html` (card com título, lista de itens, input + botão "Adicionar").
5. Um teste unitário em `tests/unit/test_<slug>.py` cobrindo criar → listar → deletar, com verificação de emissão de evento.

Se o módulo já existir (diretório já presente), o script apenas avisa (`[WARN]`) e não sobrescreve nada.

### FASE 3 — Testes (`aidd.py test`)

- `unit` (padrão): roda `pytest -v`.
- `load`: roda Locust headless por 5 segundos contra `http://localhost:3000`, se `tests/load/locustfile.py` existir.
- `all`: roda ambos em sequência.
- `e2e`: aceito como opção de CLI, mas **sem implementação correspondente** no corpo de `cmd_test` — não dispara nenhuma ação real nesta tag.

### FASE 4 — Auditoria (`aidd.py audit`)

Executa sequencialmente `G_SEGREDOS.py`, `G_QUALIDADE.py` e `G_HARNESS_COMPAT.py` como subprocessos. Se qualquer gate retornar código de saída diferente de 0, a auditoria para imediatamente (`sys.exit(1)`) e imprime `[FAIL] Gate falhou: <caminho>`. Se todos passarem, imprime `[OK] SUCESSO: Todos os gates foram 100% aprovados (exit 0)!`. **Não inclui execução de pytest** — a suíte de testes é um comando separado (Fase 3).

### FASE 5 — Deploy (`aidd.py deploy`)

- `docker` (padrão): `docker compose up -d --build`.
- `vps`: apenas orienta o usuário a rodar `bash deploy.sh` manualmente no servidor (o script não faz SSH nem publica nada por conta própria).
- `vercel`: aceito como opção de CLI, mas sem nenhuma lógica implementada em `cmd_deploy` — não executa nenhuma ação real nesta tag.

O `deploy.sh` (presente nos exemplos) faz `git pull`, `docker compose down`, `docker compose build --no-cache` e `docker compose up -d`.

### FASE 6 — Status (`aidd.py status`)

Lê `PLANO-EXECUCAO-ESTRUTURADO.json` na raiz do projeto (se existir) e imprime nome, versão e status do projeto, além de listar os subdiretórios de `src/modules/` como "Módulos Ativos". **Não gera** esse arquivo JSON — apenas o lê, caso já tenha sido criado manualmente (ver `plano-de-execucao.md` neste mesmo diretório para detalhes).

---

## 3. Output Final Entregue ao Usuário

Ao final do ciclo, o usuário obtém:
- Um projeto Python com estrutura modular (`src/core`, `src/shared`, `src/modules/<n>`).
- Uma API REST documentada dinamicamente (Swagger Studio em `/docs`, gerado por `core/openapi.py`), com playground interativo.
- Componentes de UI HTML por módulo, prontos para montar uma "Super-App" single-page.
- Testes unitários básicos por módulo.
- Três gates de qualidade mecânicos executáveis via `aidd.py audit`.
- Scripts de deploy via Docker Compose e/ou VPS shell script.

Não há, nesta tag, geração automática de servidor MCP, geração automática de `PLANO-EXECUCAO-ESTRUTURADO.json`, nem sistema de autenticação/RBAC — esses elementos aparecem apenas manualmente em alguns dos projetos de exemplo (`examples/`), não como saída padrão do fluxo `init` → `add-module` → `audit` → `deploy`.

---

*Baseado no conteúdo real de `scripts/aidd.py`, `scripts/provision_project.py`, `scripts/add_module.py` e `templates/gates/` na tag `v4.0.1`.*
