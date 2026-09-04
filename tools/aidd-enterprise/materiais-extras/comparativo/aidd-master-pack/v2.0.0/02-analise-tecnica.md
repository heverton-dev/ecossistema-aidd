# Análise Técnica e Posicionamento Realista — AIDD Master Pack

> **Documento:** Posicionamento Factual e Limitações Técnicas Reais.
> **Tag analisada:** `v2.0.0` (commit `e78ab8c` — "feat: release v2.0.0 - modular architecture, dynamic add_module, dual database, openapi swagger, docker and cloud deploy").
> **Fonte:** Snapshot extraído via `git archive v2.0.0`, examinado isoladamente (não é o HEAD atual do repositório, que já está em v5.1).
> **Objetivo:** Documentar com evidência de código o que a v2.0.0 realmente entrega, e não o que a marca "AIDD Master Pack" descreve genericamente em material promocional mais recente.

---

## 1. O Que o Pacote v2.0.0 É (Posicionamento Factual)

A **v2.0.0** é a evolução da v1.0.0 (fundação de Vertical Slice único) para um **gerador de esqueleto de projeto modular em Python puro**, sem framework web (nem Flask, nem FastAPI). Segundo o próprio `README.md` da tag, ela entrega:

1. **Modularidade sob demanda** via `python scripts/add_module.py <nome>` — cria um módulo desacoplado (`models.py`, `services.py`, `routes.py`, componente HTML, teste unitário) em segundos.
2. **Dual Database Engine** — classe `Database` em `src/core/database.py` que escolhe SQLite (modo WAL) ou PostgreSQL (via `psycopg2`) conforme a variável de ambiente `DATABASE_URL`.
3. **Registro de rotas com geração de spec OpenAPI 3.0** — classe `RouteRegistry` em `src/core/openapi.py`, com métodos `get()`/`post()` como decoradores e `generate_openapi_json()` / `get_swagger_html()`.
4. **Infraestrutura de containerização** — `Dockerfile` multi-stage, `docker-compose.yml` e `deploy.sh` (voltado a VPS Hetzner/Contabo).
5. **Teste de carga com Locust** — `tests/load/locustfile.py` genérico.
6. **3 Gates mecânicos** (`G_QUALIDADE`, `G_SEGREDOS`, `G_HARNESS_COMPAT`) em `scripts/gates/` e `templates/gates/`.
7. **Regra de design "zero emojis"** aplicada aos componentes HTML gerados.

Isso está de fato implementado no código da tag — confirmado lendo `scripts/add_module.py`, `scripts/provision_project.py` e `templates/v2/*.py` linha a linha.

---

## 2. Discrepância Importante: SKILL.md vs. Código Real

O arquivo `SKILL.md` presente nesta mesma tag já descreve recursos que **não existem em nenhum arquivo do snapshot v2.0.0**: orquestração via "ORCA Worktrees", integração com a skill `/implementacao`, "Caveman Ultra Thinking", "symlinks universais para 21 IDEs" e um "Tratado das 4 Camadas". Nenhum script, template ou exemplo da tag implementa esses itens — não há `scripts/aidd.py`, não há lógica de worktrees, não há sincronização multi-IDE, não há geração de `CONTEXTO-PROJETO.md`.

Isso indica que o `SKILL.md` é um documento de "portal"/descrição de marca que evoluiu de forma **desacoplada e adiantada** em relação ao código funcional real da tag — um padrão de posicionamento a ser lido com cautela: a descrição da skill em v2.0.0 já promete recursos que só apareceriam em versões bem posteriores (v4/v5). Quem avaliar a v2.0.0 pelo `SKILL.md` terá uma impressão de maturidade maior do que o código sustenta.

---

## 3. Limitações Técnicas Reais Identificadas no Código da Tag

| # | Limitação Técnica Real | Evidência no Código |
| :---: | :--- | :--- |
| **1** | **Nenhum servidor HTTP é gerado.** `provision_project.py` copia `database.py`, `events.py` e `openapi.py` para `src/core/`, mas não gera nenhum `main.py`/`server.py` que efetivamente instancie o `RouteRegistry`, sirva `/docs` ou dispare `/openapi.json`. O `Dockerfile` (`templates/v2/Dockerfile`) tem `CMD ["python", "src/main.py"]`, mas esse arquivo **nunca é criado** por nenhum script da tag. |
| **2** | **`requirements.txt` inexistente.** O `Dockerfile` faz `COPY requirements.txt .` mas nenhum template ou exemplo da tag contém esse arquivo. |
| **3** | **Exemplos inconsistentes entre si.** Dos 3 projetos em `examples/`, apenas `plataforma-modular-assinaturas` usa de fato a arquitetura v2.0 (`src/core/`, `src/modules/`, `EventBus`, `RouteRegistry`). Os outros dois (`catalogo-digital-whatsapp` e `plataforma-de-membros`) são projetos legados no padrão v1.0 ("AIDD 4 Camadas", `http.server.SimpleHTTPRequestHandler` manual, sem `src/core/`, sem `versao` no manifesto) — incluídos "as-is" na tag, sem upgrade. |
| **4** | **`add_module.py` gera CRUD genérico, não modelado ao domínio.** O schema criado é sempre `mod_<slug>(id, titulo, dados_json, ativo, criado_em)` — sem campos de negócio reais, sem migrações, sem suporte a PostgreSQL no `init_schema()` (o SQL usa `AUTOINCREMENT`, sintaxe específica do SQLite). |
| **5** | **`locustfile.py` é estático e não reflete os módulos gerados.** Mesmo no único exemplo genuinamente v2.0 (`plataforma-modular-assinaturas`, módulos `afiliados`/`cupons`), o `tests/load/locustfile.py` copiado testa rotas fixas (`/`, `/api/produtos`, `/docs`) que **não existem** nesse projeto. |
| **6** | **`provision_project.py` tem caminho absoluto hardcoded** (`C:\Users\trcnologia\orca\workspaces\PROJETOS Criados com IA`) e depende de uma pasta hub em `~/.agents/skills/aidd-master-pack/templates/v2` já existir no ambiente do usuário — não é um scaffolder portátil/standalone. |
| **7** | **`G_HARNESS_COMPAT` é um stub sem verificação real** — a função apenas imprime "[OK]" e retorna `sys.exit(0)` incondicionalmente, sem checar nada do ambiente. |
| **8** | **`G_QUALIDADE` só valida sintaxe (`py_compile`)** — não executa `pytest`, não varre por stubs vazios (`pass`/`TODO`), não audita acessibilidade. A suíte de testes gerada por `add_module.py` existe, mas nenhum gate a executa automaticamente. |
| **9** | **`PLANO-EXECUCAO-ESTRUTURADO.json` tem status hardcoded, não computado.** As fases `fase-01` e `fase-03` já nascem com `"status": "CONCLUIDO"` no momento da geração do projeto — antes de qualquer código ter sido escrito ou gate executado — porque o script apenas grava esses valores fixos, sem checar o sistema de arquivos. |
| **10** | **Sem autenticação, sem RBAC, sem EventBus persistente.** `EventBus` é um pub/sub em memória, single-process, sem qualquer garantia de entrega; não há módulo de auth padrão nesta tag (o `AGENTS.md` gerado nem menciona autenticação). |

---

## 4. O Que Evoluiu em Tags Posteriores (Roadmap, Visão Resumida)

Sem aprofundar (fora do escopo desta tag), o histórico de tags do repositório mostra evolução incremental clara a partir da v2.0.0:

- **v3.0.0** — adiciona uma camada de documentação interativa estilo GitBook (`/docs/guia`) aos projetos gerados.
- **v4.0.0** — introduz o "Swagger Studio" completo (3 colunas, tabelas de parâmetros dinâmicas, códigos de resposta 200/400/401/500, executor ao vivo), superando o `get_swagger_html()` simples da v2.0.0 que apenas embutia o `swagger-ui-dist` via CDN.
- **v5.x** — segundo os documentos de posicionamento do HEAD atual, chega a 7 Quality Gates bloqueantes (`G_ESTRUTURA`, `G_QUALIDADE`, `G_TESTES`, `G_CONTRACTS`, `G_SEGREDOS`, `G_HARNESS_COMPAT`, `G_SEGURANCA`), Result Pattern, RBAC, Webhooks com HMAC, servidor MCP nativo e orquestração via ORCA Worktrees — todos os recursos que o `SKILL.md` da v2.0.0 já anunciava prematuramente, mas que só passam a existir em código nessas versões futuras.

---

## 5. Conclusão

A v2.0.0 é um **incremento real e verificável sobre a v1.0.0**: ela de fato introduz modularidade sob demanda, banco dual e um registro de rotas com geração de spec OpenAPI — mas é um conjunto de **peças soltas de scaffolding**, não uma aplicação executável de ponta a ponta. Falta o elo final (servidor HTTP + `requirements.txt`) que transformaria os módulos gerados em uma API rodando de fato. Qualquer avaliação da v2.0.0 deve se basear no código (`scripts/`, `templates/`), não no `SKILL.md`, que já descreve a visão de produto de versões muito posteriores.
