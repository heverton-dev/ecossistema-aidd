# Matriz Atômica de Qualidade por Camada de Entrega — AIDD Master Pack v2.0.0

> **Tag analisada:** `v2.0.0`
> Esta matriz reflete **somente** os gates e mecanismos de qualidade que existem de fato no código desta tag (`scripts/gates/*.py` e `templates/gates/*.py`, idênticos entre si). Onde um mecanismo listado em versões posteriores (v4/v5) ainda não existe aqui, isso é declarado explicitamente como "Não existe nesta tag" — não deve ser presumido presente.

---

## 1. Critérios de Qualidade por Camada de Entrega

### A. Camada de Persistência & Banco de Dados (`src/core/database.py`)
- **Concorrência (parcial):** SQLite é aberto com `PRAGMA journal_mode=WAL;` e `PRAGMA synchronous=NORMAL;`. Não há `PRAGMA foreign_keys=ON` nem `busy_timeout` configurado explicitamente (apenas `timeout=10.0` no `sqlite3.connect`).
- **Dual Engine:** a classe `Database` decide entre SQLite e PostgreSQL (`psycopg2`) a partir de `DATABASE_URL`, mas o SQL gerado por `add_module.py` (`AUTOINCREMENT`) só é válido em SQLite — não há schema equivalente para Postgres.
- **Soft-delete / auditoria:** **Não existe nesta tag.** As tabelas geradas têm apenas `ativo` (flag booleana) e `criado_em`; não há coluna `deletado_em` nem tabela `_schema_migrations`.
- **Zero SQL Injection:** as queries geradas por `add_module.py` usam parametrização (`?`), o que é positivo, mas isso não é auditado por nenhum gate — é apenas uma convenção do template.
- **Gate validador:** nenhum gate desta tag audita especificamente a camada de banco de dados.

---

### B. Camada de Front-End & Design System (`src/static/components/*.html`)
- **Regra "Zero Emojis":** aplicada manualmente no template de `add_module.py` (nenhum emoji no HTML gerado) e reforçada em texto no `SKILL.md`, mas **não há gate automatizado** que rejeite emojis introduzidos posteriormente por um desenvolvedor/agente.
- **Sem diálogos nativos, sem WCAG, sem paginação, sem KPIs:** **Não existem nesta tag.** O componente gerado é um card simples com input + botão; não há auditoria de acessibilidade, não há tabela paginada, não há cards de métricas.
- **Gate validador:** nenhum. O único gate que toca em arquivos front-end é `G_QUALIDADE`, e apenas para arquivos `.py` (compilação de sintaxe) — HTML/JS não são verificados.

---

### C. Camada de Back-End & Regras de Negócio (`src/modules/<modulo>/services.py`)
- **CRUD parcial:** `add_module.py` gera apenas `listar()`, `criar()` e `deletar()` — **não gera** `obter_por_id()`, `atualizar()` nem `obter_metricas()`.
- **Result Pattern:** **Não existe nesta tag.** Os métodos retornam dicts ad-hoc (`{"sucesso": True, ...}`), sem um tipo `Result.ok`/`Result.fail` padronizado.
- **Anti-stubs:** o código gerado é funcional (não há `pass`/`TODO`), mas isso é garantido pelo template estático, não por um gate que varra e bloqueie stubs.
- **Emissão de eventos:** presente — toda `criar()`/`deletar()` chama `EventBus.emit(...)`, com verificação de existência do bus (`if self.events:`).
- **Linter anti-acoplamento entre módulos:** **Não existe nesta tag.** Nada impede um módulo de importar diretamente outro módulo irmão.
- **Fila de jobs assíncronos:** **Não existe nesta tag.**
- **Gate validador:** `G_QUALIDADE` cobre apenas compilação de sintaxe (`py_compile`) de todos os `.py` do projeto — não executa os testes gerados nem varre por padrões de qualidade de negócio.

---

### D. Camada de Rotas & Contratos de API (`src/core/openapi.py`)
- **OpenAPI 3.0 (não 3.1):** `RouteRegistry.generate_openapi_json()` monta um dicionário `openapi: "3.0.0"` com `paths` a partir dos decoradores `@registry.get`/`@registry.post`. Cobre `summary` e `tags`; **não gera** `body_schema` nem `query_params` estruturados.
- **Swagger UI:** `get_swagger_html()` retorna uma página estática que carrega `swagger-ui-dist` via CDN (`unpkg.com`) — depende de internet em tempo de execução; não é um "Swagger Studio" com abas/executor ao vivo (isso só aparece em v4.0.0+).
- **Nenhum servidor efetivamente serve essas rotas nesta tag** (ver `analise-tecnica.md`, item 1) — ou seja, o contrato é gerável em memória, mas não há `/docs` nem `/openapi.json` acessíveis sem que o usuário escreva o servidor HTTP manualmente.
- **MCP / JSON-RPC:** **Não existe nesta tag.**
- **Snapshot SHA-256 de contratos:** **Não existe nesta tag.**
- **CORS:** **Não existe nesta tag** (nenhum middleware ou tratamento de `OPTIONS`).
- **Gate validador:** nenhum gate desta tag audita contratos OpenAPI/MCP.

---

### E. Camada de Integração Cross-Domain (`src/core/events.py`)
- **EventBus simples:** pub/sub em memória (`defaultdict(list)`), com `on()`/`emit()`. Isolamento de erros presente: cada handler roda em `try/except` isolado, então uma falha em um listener não interrompe os demais nem o `emit()`.
- **Envelope padronizado (event_id UUID, timestamp, origin_module):** **Não existe nesta tag.** `emit()` recebe apenas `event_name` e um `data` livre, sem metadados obrigatórios.
- **Webhooks / HMAC:** **Não existem nesta tag.**
- **Gate validador:** nenhum.

---

### F. Camada de Governança, Contexto & Testabilidade
- **Manifesto de plano (`PLANO-EXECUCAO-ESTRUTURADO.json`):** existe e é gerado por `provision_project.py`, mas com **status estático hardcoded** (ver `plano-de-execucao.md`) — não reflete progresso real medido.
- **AGENTS.md / CLAUDE.md / GEMINI.md / .cursorrules:** gerados como 4 cópias idênticas de um mesmo texto — não há sincronização diferenciada por IDE, nem regras específicas por ferramenta.
- **Grafo de memória (`CONTEXTO-PROJETO.md`):** **Não existe nesta tag.**
- **Testes unitários gerados automaticamente:** sim, um teste por módulo (`tests/unit/test_<slug>.py`), cobrindo criar/listar/deletar e o evento emitido. Positivo e real.
- **Execução automática dos testes por um gate:** **Não existe nesta tag** — os testes só rodam se o desenvolvedor executar `pytest` manualmente.
- **Benchmark de concorrência, auto-remediação (`heal`), relatório de auditoria (`RELATORIO-AUDITORIA.json`):** **Não existem nesta tag.**

---

## 2. Tabela Consolidada dos 3 Gates Mecânicos Reais desta Tag

| Gate | O que Audita de Fato no Código desta Tag | Condição de Bloqueio Real |
| :--- | :--- | :--- |
| **1. G_QUALIDADE** | Percorre todos os `.py` do projeto (exceto `.git`, `node_modules`, `.venv`) e roda `py_compile` em cada um. | Qualquer erro de sintaxe Python. Não valida testes, stubs ou acessibilidade. |
| **2. G_SEGREDOS** | Varre `.py/.js/.json/.md/.env.example/.yml/.yaml` por 4 padrões regex de prefixos conhecidos (`sk-`, `AIza`, `ghp_`, `xox`) e por strings de alta entropia de Shannon (> 4.6, ≥ 32 caracteres). | Qualquer correspondência de regex ou string de alta entropia (pode gerar falsos positivos em hashes/IDs longos). |
| **3. G_HARNESS_COMPAT** | Nada. A função imprime uma mensagem de sucesso fixa e retorna `sys.exit(0)` sempre. | **Nenhuma** — é um stub, não bloqueia nada em nenhuma circunstância. |

**Gates que existem apenas em versões posteriores e NÃO estão presentes na v2.0.0:** `G_ESTRUTURA`, `G_TESTES` (execução real de `pytest`), `G_CONTRACTS` (validação de OpenAPI/MCP), `G_SEGURANCA` (auditoria OWASP/JWT/Docker non-root). Declarar isso é importante para não atribuir à v2.0.0 uma cobertura de qualidade que só a v5.x possui.

---

## 3. Resumo Honesto

A v2.0.0 tem **2 gates com verificação real** (sintaxe e varredura de segredos) e **1 gate placebo** (`G_HARNESS_COMPAT`, que sempre passa). Não há gate que rode os testes automatizados que o próprio `add_module.py` gera, o que significa que a suíte de testes só protege o projeto se o desenvolvedor lembrar de rodar `pytest` manualmente antes de cada deploy.
