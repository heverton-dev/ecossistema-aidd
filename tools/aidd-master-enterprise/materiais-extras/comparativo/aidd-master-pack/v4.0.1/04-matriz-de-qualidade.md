# Matriz Atômica de Qualidade por Camada de Entrega — AIDD Master Pack v4.0.1

> **Tag analisada:** `v4.0.1`.
> Esta matriz documenta **somente** os mecanismos de qualidade que existem de fato no código desta tag (`templates/gates/*.py`, `templates/v2/`, `scripts/`). Gates e recursos citados em versões posteriores do framework (ex.: `G_ESTRUTURA`, `G_TESTES`, `G_CONTRACTS`, `G_SEGURANCA`, RBAC, Result Pattern, migrações de schema) **não existem nesta tag** e não são listados abaixo.

---

## 1. Critérios de Qualidade por Camada de Entrega

### A. Camada de Persistência (`core/database.py`)
- **Concorrência básica:** SQLite aberto com `PRAGMA journal_mode=WAL;` e `PRAGMA synchronous=NORMAL;` (sem `busy_timeout` explícito além do `timeout=10.0` do `sqlite3.connect`).
- **Suporte opcional a PostgreSQL:** se `DATABASE_URL` começar com `postgres://`/`postgresql://`, tenta usar `psycopg2` (com fallback de erro explícito se não instalado); caso contrário, não há verificação de integridade referencial (`PRAGMA foreign_keys` não é habilitado nesta tag).
- **Zero SQL Injection nos módulos gerados:** todas as queries geradas por `add_module.py` usam parâmetros (`?`) — nenhuma interpolação de string.
- **Sem soft-delete, sem versionamento de schema:** `models.py` gerado usa `CREATE TABLE IF NOT EXISTS` simples; não há coluna de exclusão lógica nem tabela de migrações.
- **Mecanismo validador:** nenhum gate audita esta camada nesta tag (não existe `G_ESTRUTURA`). A verificação de sintaxe genérica do `G_QUALIDADE.py` (via `py_compile`) é o único gate que toca esses arquivos.

### B. Camada de Front-End (`src/static/components/*.html`, Design System "Impeccable")
- **Zero emojis em UI:** regra declarada em `templates/rules/03_impeccable.md` ("REGRA ZERO EMOJIS").
- **Ícones SVG vetoriais:** biblioteca `templates/v2/shared/ui/icons.py` com ícones inline (cart, check, lock, user, search, whatsapp, sparkles).
- **Zero diálogos nativos do navegador:** `templates/v2/shared/ui/feedback.py` / `feedback.js` implementam Toasts e Modais customizados para substituir `alert()`/`confirm()`.
- **Scrollbar de 4px e proteção de botão em linha única:** regras CSS replicadas tanto no `feedback.py` quanto no HTML gerado pelo Swagger Studio (`core/openapi.py`).
- **Mecanismo validador:** nenhum gate audita automaticamente a ausência de emojis, `alert()` ou acessibilidade nesta tag — são convenções documentadas em `templates/rules/`, não verificações mecânicas.

### C. Camada de Back-End / Regras de Negócio (`services.py`)
- **CRUD parcial gerado automaticamente:** `add_module.py` gera apenas `listar()`, `criar()` e `deletar()` — **não gera** `obter_por_id()` nem `atualizar()` (ausentes no template desta tag).
- **Emissão de eventos:** `criar()` e `deletar()` emitem eventos via `EventBus.emit()`, com `id` e dados básicos no payload — sem envelope padronizado (sem `event_id`/UUID, sem timestamp) na camada de módulo gerada; o envelope UUID (`criar_envelope_evento`) existe apenas como utilitário em `shared/events/contracts.py`, de uso opcional/manual.
- **Sem Result Pattern:** os métodos retornam dicionários simples (`{"sucesso": True, ...}`), não um objeto `Result.ok/fail` padronizado.
- **Mecanismo validador:** `G_QUALIDADE.py` garante apenas que o arquivo compila (`py_compile`) sem erro de sintaxe — não há verificação de stubs vazios, de acoplamento entre módulos ou de padrões de retorno.

### D. Camada de Rotas / API (`routes.py`, `core/openapi.py`)
- **OpenAPI 3.1.0 dinâmico:** `RouteRegistry.generate_openapi_json()` monta o documento completo a partir dos decorators `@registry.get/post/put/delete/patch`.
- **Swagger Studio interativo (3 colunas):** `RouteRegistry.get_swagger_html()` gera uma página HTML autocontida (sidebar de endpoints, documentação central, playground de requisição ao vivo com abas cURL/JavaScript/Python).
- **Sem MCP nativo gerado automaticamente:** o servidor MCP (visto em `examples/enterprise-suite-v4/src/core/mcp_server.py`) não faz parte do `core/openapi.py` nem é produzido por nenhum script desta tag — é um padrão manual replicado apenas em 2 dos 9 exemplos (`enterprise-suite-v4`, `logistica-hub-v4`).
- **Sem snapshot de contrato (hash) nem verificação de breaking changes.**
- **Mecanismo validador:** `G_HARNESS_COMPAT.py` nesta tag é um **stub** — sempre imprime `[OK]` e sai com código 0, sem checagem real de compatibilidade de rotas ou de harness.

### E. Camada de Integração Cross-Domain (`core/events.py`, `core/webhooks.py`)
- **EventBus em memória:** `defaultdict(list)` de listeners síncronos; erro em um listener é capturado e logado (`[EVENT_ERROR]`), sem interromper os demais.
- **Webhook Dispatcher assíncrono simples:** dispara requisição HTTP em uma `threading.Thread` separada; busca a URL de destino em uma tabela `configuracoes` do banco.
- **Sem assinatura HMAC, sem fila de retry, sem outbox pattern:** o payload do webhook (`event`, `timestamp`, `data`) não é assinado; falha de entrega é apenas logada (`[WEBHOOK_WARN]`), sem nova tentativa.
- **Mecanismo validador:** nenhum gate desta tag audita especificamente esta camada.

### F. Camada de Governança e Segurança (`templates/gates/`, `templates/rules/`)
- **G_SEGREDOS.py:** varre arquivos `.py/.js/.json/.md/.env.example/.yml/.yaml` por (1) regex de prefixos conhecidos de chave (`sk-`, `AIza`, `ghp_`, `xox[baprs]-`) e (2) entropia de Shannon > 4.6 bits em tokens de 32+ caracteres não totalmente maiúsculos. Bloqueia (`exit 1`) se encontrar qualquer ocorrência.
- **G_QUALIDADE.py:** compila (`py_compile`) todos os arquivos `.py` do projeto (exceto `.git`, `node_modules`, `.venv`); bloqueia se houver erro de sintaxe.
- **G_HARNESS_COMPAT.py:** stub — apenas imprime sucesso, sem lógica de verificação real.
- **Senhas:** `shared/utils/crypto.py` implementa PBKDF2-HMAC-SHA256 (100.000 iterações) com comparação de tempo constante (`hmac.compare_digest`) — mas este utilitário só é efetivamente usado se o agente/desenvolvedor chamar `hash_senha`/`verificar_senha` manualmente; nenhum módulo gerado por `add_module.py` implementa autenticação por padrão.
- **Governança de tokens (`02_golden_rules.md`):** 3 regras documentais (não chat como terminal, usar ORCA Worktrees, reiniciar sessão via Plano JSON) — são diretrizes de processo para o agente de IA, não mecanismos de código auditáveis.

---

## 2. Tabela Consolidada dos Gates Mecânicos Desta Tag

| Gate | O que Audita no Código Real | Condição de Bloqueio | Nível de Maturidade |
| :--- | :--- | :--- | :--- |
| **G_SEGREDOS** | Regex de prefixos de chave conhecidos + entropia de Shannon (limiar 4.6) em todo o projeto. | Qualquer padrão suspeito encontrado. | Funcional e real. |
| **G_QUALIDADE** | `py_compile` de todos os arquivos `.py` do projeto. | Qualquer erro de sintaxe Python. | Funcional, porém superficial (só sintaxe, não lógica/estilo/stubs). |
| **G_HARNESS_COMPAT** | Nada — imprime sucesso incondicionalmente. | Nunca bloqueia. | Stub / placeholder. |

**Gates ausentes nesta tag** (mencionados apenas em versões posteriores do framework, fora do escopo deste relatório): `G_ESTRUTURA`, `G_TESTES` (como gate — pytest só roda via `aidd.py test`, fora do `audit`), `G_CONTRACTS`, `G_SEGURANCA`.

---

*Baseado exclusivamente no conteúdo de `templates/gates/`, `templates/rules/`, `templates/v2/` e `scripts/add_module.py` na tag `v4.0.1`.*
