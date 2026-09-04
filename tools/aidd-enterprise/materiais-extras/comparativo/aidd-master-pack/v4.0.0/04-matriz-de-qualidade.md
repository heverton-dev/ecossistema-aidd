# Matriz Atômica de Qualidade por Camada de Entrega — AIDD Master Pack

> **Tag documentada:** `v4.0.0`
> **Base:** Código real de `templates/gates/*.py` e `scripts/aidd.py` (comando `audit`) extraído da tag via `git archive`.
> Esta matriz reflete **somente** os mecanismos de qualidade que existem de fato nesta tag. Onde um gate ou verificação **não existe ainda**, isso é declarado explicitamente — nada aqui foi copiado de tags posteriores (v5.x introduz `G_ESTRUTURA`, `G_TESTES`, `G_CONTRACTS`, `G_SEGURANCA`, Result Pattern, RBAC, WCAG linter etc., que **não existem em v4.0.0**).

---

## 1. Inventário Real dos Gates Mecânicos

Nesta tag existem exatamente **3 arquivos de gate** em `templates/gates/`, todos copiados sem alteração para cada novo projeto provisionado:

| Gate | Arquivo | O que audita de fato | Condição de bloqueio |
|---|---|---|---|
| **G_SEGREDOS** | `G_SEGREDOS.py` | Varre `.py/.js/.json/.md/.env.example/.yml/.yaml` com 4 regex de prefixos conhecidos (OpenAI, Google, GitHub, Slack) + cálculo de entropia de Shannon (limiar `> 4.6` bits) em tokens de 32+ caracteres | Qualquer ocorrência → `sys.exit(1)` |
| **G_QUALIDADE** | `G_QUALIDADE.py` | Compila (`python -m py_compile`) todo arquivo `.py` do repositório, ignorando `.git`, `node_modules`, `.venv` | Qualquer erro de sintaxe → `sys.exit(1)` |
| **G_HARNESS_COMPAT** | `G_HARNESS_COMPAT.py` | **Nada.** Imprime `"[OK] Harness ativo detectado com sucesso..."` e retorna `sys.exit(0)` incondicionalmente — não lê nenhum arquivo, não inspeciona nenhum ambiente | Nunca bloqueia (é um placeholder/stub) |

O comando `python scripts/aidd.py audit` executa os três em sequência via `subprocess`, interrompendo no primeiro que retornar código diferente de zero.

**O que não existe nesta tag** (e não deve ser assumido): gate de estrutura/arquitetura (`G_ESTRUTURA`), gate de execução de testes dentro da auditoria (`G_TESTES` — os testes só rodam via comando `test` separado, nunca via `audit`), gate de contratos/OpenAPI/MCP (`G_CONTRACTS`), gate de segurança amplo tipo OWASP (`G_SEGURANCA`), linter de acessibilidade/WCAG, verificação de stubs vazios (`pass`/`TODO`/`NotImplementedError`), scanner de import cruzado entre módulos, ou qualquer snapshot de contrato (SHA-256).

---

## 2. Matriz por Camada de Entrega

### A. Camada de Persistência (`database.py`)
- **O que existe:** SQLite com `PRAGMA journal_mode=WAL` e `PRAGMA synchronous=NORMAL`; suporte opcional a Postgres via `DATABASE_URL` (com fallback de erro amigável se `psycopg2` não estiver instalado); `row_factory = sqlite3.Row`; timeout de conexão de 10s.
- **O que NÃO existe:** `busy_timeout` explícito, `PRAGMA foreign_keys=ON`, soft-delete, tabela de controle de migrações (`_schema_migrations`), seed fixtures automáticas.
- **Gate que audita esta camada:** nenhum gate específico — apenas o `G_QUALIDADE` genérico (compilação de sintaxe), que não valida uso correto de conexões nem detecta connection leaks.

### B. Camada de Front-End (`static/*.html`)
- **O que existe:** convenção informal de "zero emojis" e uso de SVG (documentada em `templates/rules/03_impeccable.md`), mas **não há gate automatizado** que verifique isso no código gerado.
- **O que NÃO existe:** linter de acessibilidade, verificação de `alert()`/`confirm()`/`prompt()` nativo do navegador (o exemplo `enterprise-suite-v4` de fato usa `alert('Snippet copiado com sucesso!')` no `docs.html` do template v2 — ou seja, a própria regra "zero diálogos nativos" já é violada no código desta tag e nada a bloqueia), tabela de KPIs, paginação obrigatória.
- **Gate que audita esta camada:** nenhum.

### C. Camada de Back-End / Regras de Negócio (`services.py`)
- **O que existe:** convenção de método `criar/listar/deletar` com emissão de evento no `EventBus` a cada mutação (seguida pelo gerador `add_module.py`, mas não imposta por gate).
- **O que NÃO existe:** Result Pattern (`Result.ok`/`Result.fail`), verificação de stubs vazios, checagem de desacoplamento HTTP, fila de jobs assíncronos, checagem de import direto entre módulos irmãos.
- **Gate que audita esta camada:** nenhum — `G_QUALIDADE` só garante que o Python compila, não que a lógica esteja completa ou desacoplada.

### D. Camada de Rotas & Contratos de API (`routes.py` / `openapi.py`)
- **O que existe:** `RouteRegistry` decorator-based (`@registry.get`/`@registry.post`) que acumula endpoints e gera `/openapi.json` sob demanda; documentação HTML servida em `/docs` (CDN Swagger UI na maioria dos projetos, Studio 3-colunas custom em 2 dos 12 exemplos).
- **O que NÃO existe:** validação de que a assinatura dos decorators usada em `server.py` bate com a implementação de `RouteRegistry` (o bug documentado em `analise-tecnica.md`, seção 2, item 3, prova isso: nenhum gate captura o `TypeError` que impede o servidor `enterprise-suite-v4` de sequer iniciar), snapshot de contrato, versionamento de schema, MCP consistente entre exemplos (10 dos 12 não têm `mcp_server.py`).
- **Gate que audita esta camada:** nenhum. `G_QUALIDADE` só compila sintaxe — um `TypeError` em tempo de execução por incompatibilidade de kwargs passa despercebido porque `py_compile` não executa o código, apenas o analisa sintaticamente.

### E. Camada de Integração Cross-Domain (`events.py` / `webhooks.py`)
- **O que existe:** `EventBus` em memória (`on`/`emit`) com isolamento de erro por listener (uma exceção em um handler não derruba os demais); `WebhookDispatcher` que faz `POST` assíncrono (thread separada) para uma URL configurável, com payload `{event, timestamp, data}`.
- **O que NÃO existe:** assinatura HMAC do payload (o cabeçalho `X-Hub-Signature-256` não existe nesta tag — qualquer endpoint que receba o webhook não tem como validar a origem), envelope padronizado com `event_id`/`origin_module`, outbox transacional, retry com backoff.
- **Gate que audita esta camada:** nenhum. `G_SEGREDOS` não teria como detectar a ausência de assinatura HMAC — ele só procura segredos vazados, não a falta de um mecanismo de segurança.

### F. Camada de Governança & Testabilidade
- **O que existe:** testes unitários pytest gerados junto com cada módulo (`tests/unit/test_<slug>.py`); teste de carga opcional via Locust (`aidd.py test load`).
- **O que NÃO existe:** execução de testes dentro do `audit` (testes e gates são comandos separados e independentes — é possível rodar `audit` com sucesso mesmo que os testes estejam quebrados); manifesto de contexto de projeto (`CONTEXTO-PROJETO.md`); sincronização multi-IDE automatizada por script (os arquivos `AGENTS.md`/`CLAUDE.md`/`GEMINI.md`/`.cursorrules` encontrados nos exemplos foram escritos manualmente, não gerados); relatório de auditoria estruturado (`RELATORIO-AUDITORIA.json`) — o `audit` apenas imprime texto no console.
- **Gate que audita esta camada:** nenhum gate cobre cobertura de testes ou integridade do contexto.

---

## 3. Tabela-Resumo: Existe ou Não Existe Nesta Tag

| Mecanismo de qualidade | Existe em v4.0.0? |
|---|:---:|
| Compilação de sintaxe Python (`py_compile`) | Sim |
| Varredura de segredos por regex | Sim |
| Varredura de segredos por entropia de Shannon | Sim |
| Verificação real de compatibilidade de harness | **Não** (stub sempre `OK`) |
| Execução de testes unitários dentro do `audit` | **Não** (comando separado) |
| Gate de estrutura/arquitetura modular | **Não** |
| Gate de contratos OpenAPI/MCP | **Não** |
| Gate de segurança amplo (OWASP) | **Não** |
| Linter de acessibilidade/WCAG | **Não** |
| Anti-stub / anti-`pass` vazio | **Não** |
| Anti-acoplamento entre módulos (AST) | **Não** |
| Snapshot SHA-256 de contrato | **Não** |
| Relatório de auditoria estruturado (JSON) | **Não** |
| HMAC em webhooks | **Não** |
| RBAC / autenticação real nas rotas geradas | **Não** |

---

## 4. Leitura Honesta

A auditoria mecânica da v4.0.0 é **real, mas rasa**: ela garante que o código Python compila e que não há segredos óbvios vazando em texto plano — dois cuidados legítimos e úteis. Fora isso, não há rede de segurança automatizada: bugs de runtime (como o `TypeError` que impede `enterprise-suite-v4` de iniciar), ausência de autenticação, ausência de assinatura de webhooks e falta de testes não são capturados por nenhum gate. O terceiro gate (`G_HARNESS_COMPAT`) é, na prática, decorativo nesta versão.
