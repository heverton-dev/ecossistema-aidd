# Ciclo de Vida Completo de Uso — AIDD Master Pack

> **Tag documentada:** `v4.0.0`
> **Base:** Comportamento real de `scripts/aidd.py`, `scripts/provision_project.py`, `scripts/add_module.py` e dos gates em `templates/gates/` extraídos da tag via `git archive`.
> Este documento descreve o que **acontece de fato** ao usar esta versão — não o ciclo de vida idealizado de versões futuras.

---

## Visão Geral do Ciclo

```
┌───────────────────────────────────────────────────────────────────────────┐
│ FASE 0: OBTENÇÃO DO PACOTE                                                │
│ git clone + git checkout v4.0.0 (ou cópia da pasta da skill)              │
│ Pacote fica hospedado em: ~/.agents/skills/aidd-master-pack/              │
│   (é este caminho, hardcoded, que provision_project.py lê)                │
└───────────────────────────────────┬───────────────────────────────────────┘
                                     ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ FASE 1: PROVISIONAMENTO DO PROJETO (comando "init")                       │
│ $ python scripts/aidd.py init "Minha Plataforma"                          │
│ → chama provision_project.provision(nome)                                 │
└───────────────────────────────────┬───────────────────────────────────────┘
                                     ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ FASE 2: MODULARIZAÇÃO SOB DEMANDA (comando "add-module")                  │
│ $ python scripts/aidd.py add-module financeiro                            │
│ → gera 1 fatia vertical mínima (models, services, routes, UI, teste)      │
└───────────────────────────────────┬───────────────────────────────────────┘
                                     ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ FASE 3: VALIDAÇÃO MECÂNICA (comando "audit")                              │
│ $ python scripts/aidd.py audit                                            │
│ → roda G_SEGREDOS.py, G_QUALIDADE.py, G_HARNESS_COMPAT.py em sequência    │
└───────────────────────────────────┬───────────────────────────────────────┘
                                     ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ FASE 4: TESTES (comando "test")                                           │
│ $ python scripts/aidd.py test [unit|load|all]                             │
│ → pytest -v  e/ou  locust headless (5s, 10 usuários)                      │
└───────────────────────────────────┬───────────────────────────────────────┘
                                     ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ FASE 5: EXECUÇÃO LOCAL / OUTPUT                                           │
│ $ python src/server.py                                                    │
│ → servidor HTTP threaded na porta 3000, com rotas REST + docs             │
└───────────────────────────────────┬───────────────────────────────────────┘
                                     ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ FASE 6: DEPLOY (comando "deploy") — opcional                              │
│ $ python scripts/aidd.py deploy [docker|vps]                              │
│ → docker compose up -d --build  OU  instrução para rodar deploy.sh na VPS │
└─────────────────────────────────────────────────────────────────────────── ┘
```

---

## Detalhamento Fase a Fase

### FASE 0 — Obtenção do Pacote
Não existe um instalador. O usuário obtém o pacote via `git clone` (ou já o tem instalado como "skill" de um harness de IA). Um detalhe crítico do código: `scripts/provision_project.py` lê os templates de um caminho **absoluto e fixo do usuário original** (`~/.agents/skills/aidd-master-pack/templates/v2/` e `~/.agents/skills/aidd-master-pack/scripts/`, expandido via `os.path.expanduser('~')`). Isso significa que, para o comando `init` funcionar, o pacote precisa estar instalado nessa pasta padrão do usuário — não basta rodar os scripts a partir de uma cópia solta do repositório em qualquer diretório.

### FASE 1 — Provisionamento (`aidd.py init "<descrição>"`)
`provision_project.provision()` faz o seguinte, de forma 100% determinística (sem chamadas de IA):
1. Deriva um slug a partir das 3 primeiras palavras da descrição (ex.: "Minha Plataforma Modular" → `proj_minha-plataforma-modular`).
2. Cria a árvore de pastas: `src/core`, `src/shared`, `src/modules`, `src/static/components`, `tests/unit`, `tests/load`, `scripts/gates`.
3. Copia 4 arquivos-núcleo (`database.py`, `events.py`, `openapi.py`, `webhooks.py`) e a pasta `shared/` (utils de criptografia, validação, formatação e ícones SVG) da versão de templates **v2** (não v4).
4. Copia `Dockerfile`, `docker-compose.yml`, `deploy.sh` e `locustfile.py`.
5. Copia os scripts `aidd.py` e `add_module.py` para dentro do novo projeto (para que ele seja auto-suficiente).
6. Copia os 3 gates mecânicos.
7. Roda `git init` no novo diretório.

**O que essa fase NÃO produz:** nenhum módulo de negócio, nenhum `server.py`, nenhum arquivo `PLANO-EXECUCAO-ESTRUTURADO.json`, nenhum `mcp_server.py`, nenhum `README.md`/`CLAUDE.md`/`AGENTS.md` do projeto novo. Esses artefatos, quando existem nos projetos de exemplo do pacote, foram criados manualmente por um agente de IA seguindo a `SKILL.md`, não pelo script.

### FASE 2 — Modularização sob Demanda (`aidd.py add-module <nome>`)
Cada chamada gera, para o slug informado:
- `src/modules/<slug>/models.py` — 1 tabela SQLite (`mod_<slug>`) com `id`, `titulo`, `dados_json`, `ativo`, `criado_em`.
- `src/modules/<slug>/services.py` — classe `<Slug>Service` com `listar()`, `criar()`, `deletar()`, cada mutação emitindo um evento (`<slug>_criado`, `<slug>_deletado`) no `EventBus` se ele for injetado.
- `src/modules/<slug>/routes.py` — 3 rotas REST (`GET /api/<slug>`, `POST /api/<slug>`, `POST /api/<slug>/deletar`) registradas via `RouteRegistry` do `core.openapi` **v2** (a versão simples de 60 linhas, não o Studio 3-colunas).
- `src/static/components/<slug>.html` — 1 card de UI com input + botão "Adicionar".
- `tests/unit/test_<slug>.py` — 1 teste pytest cobrindo criar/listar/deletar e a emissão de evento.

Esse comando é puramente mecânico (regex + templates de string em Python) — não há geração de regras de negócio específicas, apenas o esqueleto CRUD genérico.

### FASE 3 — Validação Mecânica (`aidd.py audit`)
Executa em sequência, cada um como processo `subprocess` separado, abortando no primeiro `exit(1)`:
1. `G_SEGREDOS.py` — varre todos os `.py/.js/.json/.md/.env.example/.yml/.yaml` do repositório procurando padrões de chave conhecidos (OpenAI `sk-`, Google `AIza`, GitHub `ghp_`, Slack `xox`) e strings de alta entropia de Shannon (> 4.6 bits, 32+ caracteres).
2. `G_QUALIDADE.py` — compila (`py_compile`) todo arquivo `.py` do repositório e falha se houver erro de sintaxe.
3. `G_HARNESS_COMPAT.py` — imprime uma mensagem de sucesso fixa e sempre retorna código 0 (não verifica nada de fato nesta tag).

Se os três passarem, o CLI imprime `[OK] SUCESSO: Todos os gates foram 100% aprovados (exit 0)!`.

### FASE 4 — Testes (`aidd.py test [tipo]`)
- `unit` (padrão): roda `pytest -v` na raiz do projeto.
- `load`: roda Locust em modo headless por 5 segundos com 10 usuários simulados contra `http://localhost:3000` (exige o servidor já estar em execução em outro processo).
- `all`: roda ambos em sequência.
Não há suíte `e2e` implementada nesta tag, apesar de o parser da CLI aceitar essa opção — selecioná-la simplesmente não executa nenhuma ação (nenhum `if` cobre esse caso em `cmd_test`).

### FASE 5 — Execução Local / Output
Rodar `python src/server.py` (script escrito manualmente pelo agente, não gerado por um template do pacote) sobe um `http.server.HTTPServer` com `ThreadingMixIn` na porta 3000, servindo:
- `/` — SPA estático (`index.html`).
- Rotas `GET`/`POST` registradas pelos módulos.
- `/openapi.json` — schema OpenAPI 3.0/3.1 gerado dinamicamente a partir do `RouteRegistry`.
- `/docs` — documentação interativa (Swagger UI via CDN na maioria dos exemplos; Studio 3-colunas apenas em `enterprise-suite-v4` e `logistica-hub-v4`).
- `/mcp` (apenas nos 2 exemplos com `mcp_server.py`) — portal HTML + endpoint JSON-RPC 2.0 para agentes de IA.

O banco de dados é um único arquivo `.db` SQLite criado/atualizado no disco local, em modo WAL.

### FASE 6 — Deploy (opcional)
`aidd.py deploy docker` chama `docker compose up -d --build` usando o `docker-compose.yml`/`Dockerfile` copiados na Fase 1. `aidd.py deploy vps` apenas imprime uma instrução para o usuário rodar `deploy.sh` manualmente no servidor — não há automação de SSH/upload nesta tag. A opção `vercel` é aceita pelo parser de argumentos, mas não tem nenhuma lógica associada (nenhum efeito real).

---

## Resumo do Ciclo Real vs. Ciclo Prometido pela Tag

| Etapa | O que a tag v4.0.0 entrega de fato |
|---|---|
| Provisionamento | Scaffold básico nível v2.0 (SQLite, EventBus, OpenAPI simples) |
| Documentação de API | Swagger UI genérico via CDN (padrão); Studio 3-colunas só manualmente, em 2 exemplos |
| MCP | Não gerado pelo `provision_project.py`; presente só onde escrito à mão |
| Manifesto de execução | Não gerado por nenhum script (ver `plano-de-execucao.md`) |
| Qualidade | 3 gates, 2 reais + 1 stub |
| Deploy | Docker funcional; VPS manual; Vercel inexistente |
