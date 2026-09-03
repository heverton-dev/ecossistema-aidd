# Matriz Atômica de Qualidade — AIDD Master Pack v3.0.0

> **Tag analisada:** `v3.0.0`
> **Escopo:** Refletir exclusivamente os mecanismos de qualidade **presentes no código desta tag** (`templates/gates/*.py`, `scripts/aidd.py audit`). Gates de tags posteriores (`G_ESTRUTURA`, `G_TESTES`, `G_CONTRACTS`, `G_SEGURANCA`, RLS, fuzzing) são citados apenas na seção 3 como comparação explícita do que **ainda não existe**.

---

## 1. Critérios de Qualidade por Camada de Entrega (Estado Real na v3.0.0)

### A. Camada de Persistência (`database.py` / `models.py`)
- **Concorrência:** SQLite em modo WAL (`PRAGMA journal_mode=WAL;`) e `synchronous=NORMAL`. **Não há** `busy_timeout` configurado, nem `PRAGMA foreign_keys=ON`.
- **Dual DB:** Postgres suportado via `DATABASE_URL`, mas depende de `psycopg2` instalado manualmente — nenhum manifesto de dependências declara essa lib.
- **Soft-delete / auditoria:** Não existe. Os `DELETE` gerados por `add_module.py` são exclusão física (`DELETE FROM ... WHERE id = ?`).
- **Migrações de schema:** Não existe controle de versão de schema (`_schema_migrations` ou equivalente). Cada `models.py` roda `CREATE TABLE IF NOT EXISTS` sem versionamento.
- **Zero SQL Injection:** Sim, na prática — todas as queries observadas usam parâmetros (`?`), sem interpolação de string em valores.
- **Gate que audita esta camada nesta tag:** `G_QUALIDADE` (só compilação de sintaxe; **não** valida uso de context manager, nem detecta connection leak).

### B. Camada de Front-End (`src/static/*.html`)
- **Padrão visual:** Dark theme com CSS customizado inline (não há framework de utilitários como Tailwind nesta tag — os exemplos usam CSS puro escrito à mão em cada `<style>`).
- **Zero emojis:** Regra declarada em `templates/rules/03_impeccable.md`, mas **é apenas uma diretriz textual** — não há gate ou linter automatizado que a valide no código desta tag.
- **Diálogos nativos (`alert`/`confirm`):** Sem gate que proíba; não verificado automaticamente.
- **Acessibilidade (WCAG):** Sem gate ou checklist automatizado nesta tag.
- **Documentação GitBook (`docs.html`):** Presente manualmente em 3 dos 6 exemplos (ver `analise-tecnica.md`), sem gate que garanta sua existência/consistência.
- **Gate que audita esta camada nesta tag:** Nenhum. `G_QUALIDADE` só olha arquivos `.py`.

### C. Camada de Back-End / Regras de Negócio (`services.py`)
- **CRUD gerado por `add_module.py`:** Apenas `listar()`, `criar()`, `deletar()`. Não há `atualizar()`/`obter_por_id()` no template automático (implementados manualmente apenas nos exemplos V3, caso a caso).
- **Result Pattern:** Não existe. Os métodos retornam dicionários ad-hoc (`{"sucesso": True, ...}`), sem um tipo padronizado de erro/sucesso.
- **Anti-stubs (`pass`, `TODO`, `NotImplementedError`):** Sem gate que proíba isso nesta tag.
- **Desacoplamento HTTP:** Os serviços não recebem objetos HTTP diretamente — recebem dicts/primitivos, o que é seguido consistentemente nos exemplos.
- **Emissão de eventos:** Sim — `criar()`/`deletar()` chamam `self.events.emit(...)` quando um `EventBus` é injetado. Não há envelope padronizado (sem `event_id` UUID, sem `timestamp` obrigatório).
- **Linter anti-acoplamento entre módulos:** Não existe nesta tag.
- **Gate que audita esta camada nesta tag:** `G_QUALIDADE` (só sintaxe).

### D. Camada de Rotas e Contratos de API (`routes.py` / `openapi.py`)
- **OpenAPI:** Versão **3.0.0** (não 3.1), gerada dinamicamente a partir do `RouteRegistry` (`@registry.get`/`@registry.post`).
- **Swagger UI:** Disponível em `/docs`, mas carregado via CDN externo (`unpkg.com/swagger-ui-dist@5`) — sem funcionamento offline.
- **MCP (Model Context Protocol):** Não existe nesta tag.
- **Snapshot/hash de contrato:** Não existe.
- **CORS:** Não há middleware de CORS/preflight automático nos `server.py` observados.
- **Gate que audita esta camada nesta tag:** Nenhum gate dedicado a contratos.

### E. Camada de Integração Cross-Domain (`events.py` / `webhooks.py`)
- **EventBus:** Pub/sub em memória, single-process. Um listener com exceção é capturado e logado (`print`), sem interromper os demais.
- **Webhooks:** Disparo assíncrono via thread para uma URL lida da tabela `configuracoes`. **Sem assinatura HMAC**, sem retentativa, sem fila de reentrega — falha é apenas logada (`print`).
- **Gate que audita esta camada nesta tag:** Nenhum.

### F. Camada de Testes e Governança (`tests/unit/`, `AGENTS.md`)
- **Testes gerados por `add_module.py`:** Cobrem o ciclo criar → listar → deletar do módulo recém-criado (teste real, não trivial).
- **Testes dos exemplos V3 (`test_modules.py`):** Genéricos — testam apenas o `EventBus`, não os serviços de domínio reais criados manualmente (ex.: `ContasService` não é testado em `erp-financeiro-v3`).
- **Teste de carga (Locust):** Presente, mas com endpoints genéricos (`/api/produtos`) que não correspondem necessariamente às rotas reais do projeto.
- **Governança multi-IDE:** `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.cursorrules` presentes apenas nos 3 exemplos legados (`catalogo-digital-whatsapp`, `plataforma-de-membros`, `plataforma-modular-assinaturas`) — os 3 exemplos V3 novos **não** possuem esses arquivos de governança.
- **Gate que audita esta camada nesta tag:** `scripts/aidd.py test unit` (executa pytest), sem gate de cobertura mínima.

---

## 2. Tabela Consolidada dos Gates Mecânicos Existentes na v3.0.0

| Gate | O que Audita Realmente | Condição de Bloqueio | Limitação Conhecida |
| :--- | :--- | :--- | :--- |
| **G_SEGREDOS** | Regex de prefixos conhecidos (`sk-`, `AIza`, `ghp_`, `xox`) + entropia de Shannon (limiar > 4.6 bits) em arquivos `.py/.js/.json/.md/.env.example/.yml/.yaml`. | Qualquer match de regex ou string de alta entropia (32+ caracteres, não totalmente maiúscula). | Pode gerar falsos positivos em hashes/UUIDs legítimos; não distingue segredo real de dado de teste. |
| **G_QUALIDADE** | Compila cada arquivo `.py` do projeto com `py_compile`. | Qualquer erro de sintaxe. | Não executa testes, não analisa lógica, não audita front-end. |
| **G_HARNESS_COMPAT** | Nada — apenas imprime uma mensagem fixa. | Nunca falha (`sys.exit(0)` incondicional). | É um gate "sempre verde"; não verifica de fato o harness/IDE em uso. |

`scripts/aidd.py audit` executa os três em sequência e interrompe no primeiro que retornar código de saída diferente de zero.

---

## 3. O Que Ainda NÃO Existe Nesta Tag (Declaração Explícita)

Para evitar sobre-representar a maturidade da v3.0.0, os itens abaixo **não têm nenhuma implementação** no snapshot desta tag — todos aparecem apenas em versões posteriores (v4.x/v5.x) do repositório:

- `G_ESTRUTURA` (validação de fatias/Clean Architecture, anti-acoplamento entre módulos)
- `G_TESTES` (gate dedicado de execução/cobertura de testes com bloqueio)
- `G_CONTRACTS` (validação e snapshot SHA-256 de contratos OpenAPI/MCP)
- `G_SEGURANCA` (auditoria OWASP, JWT, Docker non-root, etc.)
- Autenticação/autorização (JWT, RBAC, PBKDF2 implementado em código)
- Row-Level Security (RLS) e reescrita de queries multi-tenant
- Fuzzing contínuo de APIs
- Servidor MCP nativo (Model Context Protocol)
- Result Pattern padronizado, soft-delete, migrações de schema versionadas
- Geração automática (via script/template) da documentação estilo GitBook — existe apenas como arquivo estático manual em 3 dos 6 exemplos
