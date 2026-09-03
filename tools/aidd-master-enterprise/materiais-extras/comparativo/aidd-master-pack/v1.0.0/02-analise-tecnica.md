# Análise Técnica e Posicionamento Realista — AIDD Master Pack `v1.0.0`

> **Tag analisada:** `v1.0.0`
> **Commit:** `729ce3e` — "docs: standardize master packages v1, v2, v3, v4 naming and structure" (31/08/2026)
> **Nome interno do pacote:** `aidd-master-pack-v1`
> **Subtítulo oficial (README/SKILL.md):** *"AIDD v1.0 — Fundação Modular Vertical Slice (Esqueleto Inicial com SQLite WAL, Pytest e Gates Mecânicos)"*

Este documento descreve exclusivamente o que existe no snapshot da tag `v1.0.0`, extraído via `git archive v1.0.0`. Nenhuma funcionalidade das tags posteriores (v2.0.0 em diante) é atribuída a esta versão, exceto quando citada explicitamente como "roadmap/evolução futura".

---

## 1. O que a tag `v1.0.0` realmente contém

A tag entrega um pacote de **5 elementos**, sem código de aplicação "vivo" fora da pasta `examples/`:

| Item | Caminho | Natureza |
|---|---|---|
| Micro-CLI do framework | `scripts/aidd.py` | Único ponto de entrada (`init`, `add-module`, `test`, `audit`, `deploy`, `status`) |
| Gerador de módulo | `scripts/add_module.py` | Gera `models.py` + `services.py` + `routes.py` + componente HTML + teste, a partir de 1 nome de módulo |
| Provisionador de projeto | `scripts/provision_project.py` | Cria a estrutura de pastas de um novo projeto e copia o "shared kernel" |
| Gates mecânicos | `templates/gates/G_QUALIDADE.py`, `G_SEGREDOS.py`, `G_HARNESS_COMPAT.py` | 3 scripts Python isolados, sem framework de teste, chamados via `subprocess` |
| Regras/skill agêntica | `SKILL.md`, `templates/rules/*.md` | Instruções em prosa para o agente de IA seguir (não é código executável) |
| Projetos de referência | `examples/*` (12 pastas) | Saídas geradas previamente pelo próprio framework, usadas como prova de conceito |

Não existe pasta `src/` própria do pacote — todo código de aplicação (`Database`, `EventBus`, `RouteRegistry`, `WebhookDispatcher`) mora em `templates/v2/*.py`, que é copiado para dentro de cada novo projeto no momento do `provision_project.py`.

### 1.1 Shared Kernel (`templates/v2/`)

Apesar do nome da tag ser `v1.0.0`, o próprio código-fonte do "shared kernel" já se autodenomina "v2" em várias strings (`print(f"[AIDD MASTER PACK v2.0]...")` em `provision_project.py`, `User-Agent: AIDD-Webhook-Dispatcher/2.0` em `webhooks.py`, `[GATE G_SEGREDOS v2.0 - Shannon Entropy Engine]` em `G_SEGREDOS.py`, `version="2.0.0"` como default do OpenAPI). Isso é uma evidência concreta de que as tags `v1.0.0`–`v4.x` **não representam uma progressão histórica linear e limpa**: foram todas cortadas no mesmo dia (31/08/2026, entre 21h12 e 00h13) a partir de um único histórico de commits em evolução contínua, e a numeração da tag reflete uma convenção de nomenclatura retroativa, não o estado real de maturidade do código em cada corte. `v1.0.0` foi inclusive tagueada **depois** de `v2.0.0` e `v3.0.0` no mesmo commit.

O kernel entrega, de fato:
- `Database` — wrapper fino sobre `sqlite3` (WAL mode) com suporte opcional a Postgres via `psycopg2` (se instalado).
- `EventBus` — pub/sub síncrono em memória (`dict` de listeners), sem persistência, sem retry, sem fila.
- `RouteRegistry` — roteador HTTP artesanal (decorators `@get`/`@post`) que também gera um JSON no formato OpenAPI 3.0 e uma página Swagger UI (carregada via CDN externo, sem vendoring).
- `WebhookDispatcher` — dispara um `POST` HTTP em thread separada (`threading.Thread`, sem pool, sem retry, sem fila de falhas) para uma URL configurável salva em uma tabela `configuracoes`.

### 1.2 Servidor de aplicação

Os projetos gerados usam **`http.server` puro da stdlib** (`ThreadingMixIn` + `HTTPServer`), não Flask, FastAPI, Django ou qualquer framework web. O roteamento é feito manualmente dentro do handler, comparando `self.path` contra o dicionário de rotas do `RouteRegistry`. Não há middleware, não há validação de schema de request além do que cada `service.py` decide fazer na mão.

---

## 2. Limitações técnicas reais

1. **Nenhum CI/CD.** Não existe `.github/workflows` nem qualquer outro pipeline automatizado em toda a árvore da tag. "Rodar os gates" é uma ação manual (`python scripts/aidd.py audit`).
2. **`Dockerfile` quebrado por padrão.** `templates/v2/Dockerfile` faz `COPY requirements.txt .`, mas **não existe nenhum `requirements.txt`** em lugar algum da tag (nem no pacote raiz, nem em nenhum dos 12 exemplos). O build Docker documentado no README v2 falharia sem o usuário criar esse arquivo manualmente.
3. **`G_HARNESS_COMPAT.py` é um gate de fachada.** O código inteiro do gate é: imprimir uma mensagem de sucesso e retornar `sys.exit(0)`. Ele não verifica IDE, ambiente ou capacidades reais — sempre passa.
4. **`G_QUALIDADE.py` só verifica sintaxe.** Ele roda `py_compile` em todo `.py` do repositório; não executa lint, não mede cobertura, não valida estilo. A suíte `pytest` só roda separadamente via `aidd.py test`, e falhas em `pytest` **não bloqueiam** o gate `audit` (que só chama os 3 scripts em `gates/`, não o pytest).
5. **`G_SEGREDOS.py` é heurístico e ingênuo.** Usa 4 regex de prefixos conhecidos (`sk-`, `AIza`, `ghp_`, `xox`) mais um cálculo de entropia de Shannon (>4.6 bits) para strings de 32+ caracteres. Sujeito a falso positivo (qualquer hash, UUID ou string aleatória de teste dispara o gate) e falso negativo (segredos com baixa entropia, ou divididos em concatenação, passam despercebidos).
6. **Sem autenticação/autorização real de framework.** Cada exemplo reimplementa login/hash na mão (ver `src/auth.py` de cada projeto); não há middleware de sessão compartilhado no kernel v1.
7. **EventBus sem garantias.** É síncrono, em processo único, sem persistência — se o processo cair no meio de um handler, os efeitos posteriores (ex.: disparo de webhook) simplesmente não acontecem. Não há reprocessamento nem fila morta.
8. **Webhook "fire-and-forget".** `WebhookDispatcher.disparar()` cria uma thread solta por evento, sem limite de threads simultâneas, sem retry e sem registro de falha persistente — apenas um `print` no console.
9. **Inconsistência entre os próprios exemplos oficiais.** Nem todo projeto em `examples/` segue a mesma estrutura: apenas 5 das 12 pastas têm `PLANO-EXECUCAO-ESTRUTURADO.json`; `helpdesk-sla-v2` não tem `CLAUDE.md`; `catalogo-digital-v3` mistura uma implementação monolítica antiga (`src/services.py`, 644 linhas, com sua própria classe `LojaService`) **e** uma implementação modular nova (`src/modules/*/backend/`) coexistindo no mesmo projeto, com o teste de integração (`tests/test_catalogo.py`) validando apenas a versão monolítica antiga.
10. **Testes gerados automaticamente são rasos.** O teste que `add_module.py` gera para cada novo módulo cobre apenas criar/listar/deletar via SQLite em memória — não testa rotas HTTP, nem contratos OpenAPI, nem concorrência, nem falhas.
11. **Sem gestão de segredos/ambiente.** Não há `.env.example`, não há biblioteca de configuração — variáveis como `DATABASE_URL` são lidas via `os.getenv` com defaults embutidos no código.
12. **`provision_project.py` tem caminho de instalação hard-coded** (`C:\Users\trcnologia\orca\workspaces\...` e `~/.agents/skills/aidd-master-pack/...`), o que o torna não-portável fora da máquina original sem edição manual.

---

## 3. O que a versão entrega de fato (pontos positivos)

- Um **fluxo mínimo e coerente** de "gerar módulo → escrever regra de negócio → rodar teste → rodar gate → subir Docker" funciona de ponta a ponta nos exemplos testados (`pytest` passa em `examples/catalogo-digital-v3`).
- Separação vertical por módulo (`models.py` / `services.py` / `routes.py` / componente de UI / teste) já está presente desde este corte, mesmo sem camada `frontend/`/`backend/` explícita em todos os exemplos.
- Gates determinísticos (ainda que simples) existem desde o início — não dependem de LLM para rodar, só de Python puro.
- SQLite com WAL mode configurado corretamente (`PRAGMA journal_mode=WAL`, `synchronous=NORMAL`) desde o primeiro corte.
- Regras de segurança básicas documentadas (`04_security.md`): PBKDF2-HMAC-SHA256 para senha, comparação em tempo constante, queries parametrizadas.

## 4. Posicionamento realista

`v1.0.0` é um **kit de scaffolding de projeto único-arquivo/único-processo**, adequado para protótipos e MVPs pequenos rodados localmente ou em uma única VPS via Docker Compose. Não é, nesta tag, uma plataforma multi-serviço, multi-tenant ou de alta disponibilidade — não existe orquestração de múltiplos módulos além de import direto no `server.py`, não existe fila de mensagens, não existe camada de cache, e a "API" é uma implementação artesanal sobre `http.server`.

### Roadmap (citado apenas para contexto — não implementado nesta tag)

As tags seguintes da série (`v2.0.0` em diante) introduzem, segundo os nomes dos próprios pacotes e READMEs de topo do repositório, capacidades como padronização cross-projeto, EventBus mais robusto, MCP server nativo, Swagger Studio completo e Super-App UI unificada. Nenhum desses itens faz parte do conteúdo real da tag `v1.0.0` — eles são citados aqui apenas para situar o leitor na trajetória do produto, não como funcionalidade desta versão.
