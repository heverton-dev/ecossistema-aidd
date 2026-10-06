# Matriz Atômica de Qualidade — AIDD Master Pack v4.2.0

> **Tag analisada:** `v4.2.0`.
> Esta matriz lista **apenas** os mecanismos de qualidade que existem de fato no código desta tag. Recursos que só aparecem em tags posteriores (ex.: `G_ESTRUTURA`, `G_TESTES`, `G_CONTRACTS`, Result Pattern, soft-delete, CORS middleware, RBAC avançado) foram deliberadamente **omitidos** ou marcados como ausentes, para não confundir o leitor com capacidades de versões futuras.

---

## 1. Gates mecânicos existentes nesta tag

| Gate | Localização | O que audita de fato | Integrado a `aidd.py audit`? |
| :--- | :--- | :--- | :---: |
| **G_QUALIDADE** | `templates/gates/G_QUALIDADE.py` | Compila (`py_compile`) todo arquivo `.py` do projeto e falha se houver erro de sintaxe. Não analisa stubs, não faz lint semântico. | Sim |
| **G_SEGREDOS** | `templates/gates/G_SEGREDOS.py` | Varre `.py/.js/.json/.md/.env.example/.yml/.yaml` por (a) padrões regex de chaves conhecidas (`sk-`, `AIza`, `ghp_`, `xox`) e (b) tokens com entropia de Shannon > 4.6 bits. | Sim |
| **G_HARNESS_COMPAT** | `templates/gates/G_HARNESS_COMPAT.py` | Apenas imprime que o "harness" foi detectado e retorna sucesso (`sys.exit(0)`) — não executa nenhuma verificação condicional real nesta tag. | Sim |
| **G_SEGURANCA** | `scripts/gates/G_SEGURANCA.py` | 7 camadas: headers OWASP, JWT HS256 (geração/tampering/expiração), PBKDF2, varredura estática de SQL Injection, config Nginx, hardening de Dockerfile, modo WAL + tabela `logs_auditoria`, `securitySchemes.bearerAuth` no OpenAPI. | **Não** — precisa ser chamado manualmente; não é copiado automaticamente para novos projetos (só está presente em 2 dos 13 exemplos do pacote). |

Não existem nesta tag os gates `G_ESTRUTURA` (anti-acoplamento/layout), `G_TESTES` (obrigatoriedade de pytest passar) ou `G_CONTRACTS` (snapshot de contratos). A execução de testes (`pytest`) só ocorre via `aidd.py test`, um comando independente e **não bloqueante** do fluxo de `audit`.

---

## 2. Critérios de qualidade por camada de entrega (somente o que existe nesta tag)

### A. Camada de Persistência (`templates/v2/database.py`, `models.py` gerado por `add_module.py`)
- SQLite com `PRAGMA journal_mode=WAL;` e `PRAGMA synchronous=NORMAL;`, timeout de conexão de 10s.
- Suporte opcional a PostgreSQL via `psycopg2` — **não é dependência embutida**; o próprio código levanta `RuntimeError` orientando `pip install psycopg2-binary` se ausente.
- Cada módulo gerado recebe uma tabela genérica única: `mod_<slug>(id, titulo, dados_json, ativo, criado_em)` com índice em `ativo`. Não há colunas de auditoria (`atualizado_em`), soft-delete ou versionamento de schema.
- **Ausentes nesta tag:** `PRAGMA foreign_keys=ON`, `busy_timeout`, soft-delete, tabela `_schema_migrations`.
- **Gate validador:** nenhum gate audita especificamente o schema ou o modo WAL em tempo de `aidd.py audit` — a camada 6 do `G_SEGURANCA.py` verifica WAL e a tabela `logs_auditoria`, mas apenas quando esse gate é chamado manualmente.

---

### B. Camada de Front-End (`src/static/`, componente HTML gerado por `add_module.py`)
- `add_module.py` gera um bloco HTML de "card" por módulo, com input de texto e botão de adicionar — sem framework de build, HTML/CSS/JS servidos como estáticos.
- O README/SKILL.md desta tag menciona um "Impeccable Design System" com zero emojis e scrollbars de 4px, mas **nenhum gate desta tag audita isso automaticamente**: `G_QUALIDADE` só roda `py_compile` em arquivos Python, não faz lint de HTML/JS, não verifica ausência de `alert()`/`confirm()` nem WCAG.
- **Gate validador:** nenhum (verificação apenas manual/visual nesta tag).

---

### C. Camada de Back-End / Regras de Negócio (`services.py` gerado por `add_module.py`)
- CRUD **parcial**: `listar()`, `criar()`, `deletar()`. Não há `atualizar()`/`update`, `obter_por_id()` nem `obter_metricas()` no template gerado.
- Emissão de eventos: `criar()` e `deletar()` chamam `self.events.emit(...)` (quando um `EventBus` é injetado); `listar()` não emite evento (não deveria, é leitura).
- **Ausentes nesta tag:** Result Pattern (`Result.ok`/`Result.fail`), proibição formal de stubs (`pass`/`...`/`NotImplementedError`) verificada por gate, linter AST anti-acoplamento entre módulos irmãos, fila de jobs assíncrona.
- **Gate validador:** `G_QUALIDADE` (somente compila o arquivo; não valida completude do CRUD nem ausência de stubs).

---

### D. Camada de Rotas e Contratos de API (`routes.py` gerado, `templates/v2/openapi.py`)
- `RouteRegistry` (`openapi.py`, ~1000 linhas) suporta os métodos `GET/POST/PUT/DELETE/PATCH` e monta dinamicamente um spec OpenAPI 3.1 com respostas padrão (`200/400/401/500`) e `securitySchemes.bearerAuth`.
- O `routes.py` gerado por `add_module.py`, porém, só registra `GET /api/<mod>`, `POST /api/<mod>` e `POST /api/<mod>/deletar` — nenhuma rota `PUT`/atualização é criada automaticamente, mesmo o `RouteRegistry` suportando o método.
- **Ausentes nesta tag:** middleware CORS/preflight automático (não localizado em `server.py` dos exemplos analisados), snapshot SHA-256 de contratos, gate `G_CONTRACTS`.
- **Gate validador:** nenhum gate audita contratos automaticamente; a camada 7 do `G_SEGURANCA.py` apenas confere se `bearerAuth` está presente no spec gerado, quando executado manualmente.

---

### E. Camada de Integração Cross-Domain (`templates/v2/events.py`, `templates/v2/webhooks.py`)
- `EventBus` (16 linhas): `defaultdict(list)` de listeners, métodos `.on()`/`.emit()`. Não há `event_id`, timestamp ou origem padronizados no envelope — o evento é só `(nome, dados)`.
- `WebhookDispatcher` (`webhooks.py`, ~1470 linhas, a maior parte é um catálogo de eventos de exemplo e a página HTML do "Webhook Studio"): dispara requisições HTTP assinadas com HMAC-SHA256, enviando os cabeçalhos `X-Webhook-Signature`, `X-Hub-Signature-256`, `X-Webhook-Event`, `X-Webhook-Delivery` e `X-Webhook-Timestamp`. Essa é uma funcionalidade real e substancial já presente nesta tag.
- **Ausentes nesta tag:** persistência de eventos pendentes (tudo em memória — se o processo cair, eventos não persistidos se perdem), retry configurável verificado por teste automatizado.
- **Gate validador:** nenhum gate dedicado; a segurança da assinatura HMAC é indiretamente coberta pela filosofia do `G_SEGURANCA.py`, mas esse gate não testa o dispatcher de webhooks especificamente.

---

### F. Camada de Governança e Testabilidade (`templates/rules/*.md`, `tests/unit/`)
- Regras curtas em Markdown: `01_layers.md` (camadas do "Tratado AIDD"), `02_golden_rules.md` (3 regras de economia de tokens), `04_security.md`, `04_cross_project.md`, `05_production_vps.md`.
- Testes unitários: `add_module.py` gera 1 teste por módulo cobrindo criar → listar → deletar (coerente com o CRUD parcial da camada C).
- Teste de carga: `templates/v2/locustfile.py` fornecido como template, disparável via `aidd.py test load`.
- Arquivos multi-IDE (`CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, `.cursorrules`) existem em alguns projetos de exemplo (ex.: `catalogo-digital-v3`), mas **não são gerados por nenhum script** desta tag — são artefatos incluídos manualmente nos exemplos, não uma funcionalidade automatizada do framework.
- **Ausentes nesta tag:** `SPEC-ARQUITETURA.md`, `CONTEXTO-PROJETO.md`, `RELATORIO-AUDITORIA.json`, templates de subagentes por papel, benchmark de concorrência (`aidd bench`), auto-remediação (`aidd heal`).
- **Gate validador:** `G_QUALIDADE`, `G_SEGREDOS`, `G_HARNESS_COMPAT` (via `aidd.py audit`) e, manualmente, `G_SEGURANCA`.

---

## 3. Tabela consolidada dos gates desta tag

| Gate | Bloqueia o quê | Executado automaticamente por |
| :--- | :--- | :--- |
| **G_QUALIDADE** | Qualquer erro de sintaxe Python (`py_compile`). | `aidd.py audit` |
| **G_SEGREDOS** | Padrões de chave conhecidos ou strings de alta entropia (> 4.6 bits). | `aidd.py audit` |
| **G_HARNESS_COMPAT** | Nada de fato (sempre retorna sucesso nesta tag). | `aidd.py audit` |
| **G_SEGURANCA** | Qualquer falha nas 7 camadas de segurança (headers, JWT, SQLi, Nginx, Docker, WAL, OpenAPI). | Nenhum comando — só execução manual (`python scripts/gates/G_SEGURANCA.py`). |
