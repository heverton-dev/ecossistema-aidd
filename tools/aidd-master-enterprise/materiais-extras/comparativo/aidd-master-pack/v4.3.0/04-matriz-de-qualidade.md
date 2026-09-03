# Matriz Atômica de Qualidade — AIDD Master Pack `v4.3.0`

> **Tag analisada:** `v4.3.0`
> Esta matriz lista **apenas** os mecanismos de qualidade comprovadamente presentes no código desta tag. Gates de gerações posteriores (`G_ESTRUTURA`, `G_TESTES`, `G_CONTRACTS`) **não existem** nesta versão e não são listados aqui.

---

## 1. Critérios de Qualidade por Camada de Entrega

### A. Camada de Persistência (`core/database.py` / `models.py` de cada módulo)
- **Concorrência:** SQLite aberto com `PRAGMA journal_mode=WAL;` e `PRAGMA synchronous=NORMAL;` (`templates/v2/database.py`). `timeout=10.0` na conexão.
- **Suporte experimental a Postgres:** `Database` detecta URLs `postgres://`/`postgresql://` e tenta `psycopg2`, mas esse caminho não é coberto por nenhum gate nem exemplo funcional nesta tag.
- **Schema por módulo:** cada módulo gerado por `add_module.py` define seu próprio `init_schema(conn)` com `CREATE TABLE IF NOT EXISTS mod_<slug>` e um índice em `ativo`. Não há migração versionada nem soft-delete (linha `ativo INTEGER DEFAULT 1` funciona como flag simples, sem coluna de auditoria de exclusão).
- **Parametrização:** todas as queries observadas usam placeholders (`?`), auditado estaticamente pelo `G_SEGURANCA.py` (Camada 3 — varredura contra SQL Injection).
- **Gate validador nesta tag:** `G_SEGURANCA.py` (Camada 3 e Camada 6 — auditoria de modo WAL).

---

### B. Camada de Front-End (`src/static/*.html`, `templates/rules/03_impeccable.md`)
- **Design System "Impeccable":** regras obrigatórias documentadas — zero emojis (ícones SVG Lucide/Heroicons), zero diálogos nativos do SO (`alert`/`confirm` proibidos, substituídos por `showToast()`/`showConfirm()` do *shared kernel*), header de linha única (`white-space: nowrap`, `flex-shrink: 0`), scrollbars padronizadas de 4px, botões sem quebra de linha.
- **Escala tipográfica fixa** documentada em tabela (`--text-2xl` a `--text-xs`, `--font-mono`).
- **Paleta de cores fixa** (glassmorphism em tons de `#020617`/`#3b82f6`).
- **Componente gerado automaticamente** por módulo (`add_module.py`), com card, container de itens e input de criação — mas sem paginação, sem busca e sem indicadores de KPI.
- **Gate validador nesta tag:** nenhum gate audita CSS/HTML automaticamente; a conformidade com o Impeccable depende de disciplina manual/do agente de IA, não de verificação mecânica.

---

### C. Camada de Back-End / Regras de Negócio (`services.py` de cada módulo)
- **CRUD parcial gerado automaticamente:** `criar()`, `listar()` e `deletar()` são gerados por `add_module.py`. **Update não é gerado** — precisa ser escrito manualmente, apesar do `SKILL.md` anunciar "Full CRUD Diligente".
- **Emissão de eventos:** toda mutação (`criar`, `deletar`) dispara `self.events.emit("<slug>_criado" / "<slug>_deletado", {...})` via `EventBus`.
- **Sem padrão de retorno estruturado:** os métodos devolvem dicionários ad-hoc (`{"sucesso": True, ...}`), sem um `Result`/`Either` uniforme — divergências de formato de erro ficam a critério de cada implementação manual.
- **Sem proibição automática de stubs:** nenhum gate desta tag varre o código em busca de `pass`/`TODO`/`NotImplementedError` — só `G_QUALIDADE.py`, que apenas garante que o arquivo compila.
- **Gate validador nesta tag:** `G_QUALIDADE.py` (compilação), `G_SEGURANCA.py` (Camada 2 — hashing de senha PBKDF2 e JWT HS256 quando aplicável ao módulo de auth).

---

### D. Camada de Rotas / Contratos de API (`routes.py`, `core/openapi.py`)
- **OpenAPI 3.1 dinâmico:** rotas registradas via `RouteRegistry` com `@registry.get`/`@registry.post`, `summary`, `description`, `body_schema`/`body_example` e `responses` — compõem o `/openapi.json` e o Swagger Studio em `/docs`.
- **Portal MCP:** `/mcp` (portal HTML) e `/api/mcp/rpc` (JSON-RPC 2.0) expõem as rotas registradas como ferramentas para agentes de IA — implementado por domínio (ex.: `LogisticaMCPServer`), não gerado automaticamente por `add_module.py` para módulos novos.
- **Sem verificação de contrato:** não existe *snapshot* de schema nem hash de verificação de quebra de contrato nesta tag (isso só aparece em gerações posteriores, no `G_CONTRACTS`).
- **CORS:** presente no servidor de referência (`src/server.py`), mas não auditado por nenhum gate.
- **Gate validador nesta tag:** `G_SEGURANCA.py` (Camada 7 — presença de `bearerAuth` em `components.securitySchemes` do spec OpenAPI).

---

### E. Camada de Integração Cross-Domain (`core/events.py`, `core/webhooks.py`)
- **EventBus:** pub/sub simples em memória, single-process — sem persistência de eventos pendentes, sem *outbox*.
- **Webhook Configuration Studio v4 (novidade desta tag):** dashboard em `/webhooks` com CRUD completo de assinantes (`GET/POST /api/webhooks`, `/atualizar`, `/toggle`, `/excluir`), catálogo de eventos disponíveis (`/api/webhooks/catalog`), simulador de disparo (`/api/webhooks/testar`), histórico de logs (`/api/webhooks/logs`) e reenvio manual (`/api/webhooks/logs/reenviar`).
- **Assinatura de segurança:** disparos assinados com HMAC-SHA256 (`X-Webhook-Signature`/`X-Hub-Signature-256`, conforme `templates/rules/04_cross_project.md`).
- **Gate validador nesta tag:** `G_SEGURANCA.py` (não há um gate dedicado a eventos/webhooks; a verificação funcional é feita por `scripts/test_live.py`, que testa o simulador e confere a assinatura HMAC devolvida).

---

### F. Camada de Governança e Testabilidade (`tests/unit/`, `scripts/gates/`, `templates/rules/`)
- **Regras determinísticas versionadas:** `templates/rules/01_layers.md` (4 camadas do "Tratado AIDD"), `02_golden_rules.md` (3 regras anti-estouro de tokens), `03_impeccable.md` (design system), `04_cross_project.md` (arquitetura cross-domain), `04_security.md` (segurança), `05_production_vps.md` (deploy).
- **Testes unitários gerados por módulo:** um teste por domínio (`tests/unit/test_<slug>.py`), cobrindo criação, listagem e exclusão com verificação de evento emitido — mas sem asserção de mutação de estado (não compara "antes vs. depois" do mesmo registro).
- **Sem grafo de memória de projeto** (`CONTEXTO-PROJETO.md` não existe nesta tag) e sem *spec* estruturada em 3 níveis — ambos surgem só na série v5.
- **Gate validador nesta tag:** `G_SEGREDOS.py`, `G_QUALIDADE.py`, `G_HARNESS_COMPAT.py` (via `aidd.py audit`), mais `G_SEGURANCA.py` (execução manual).

---

## 2. Tabela Consolidada dos Gates Mecânicos Existentes na v4.3.0

| Gate | Localização no pacote | O que audita de fato | Plugado em `aidd.py audit`? |
| :--- | :--- | :--- | :---: |
| **G_SEGREDOS** | `templates/gates/G_SEGREDOS.py` | Regex de prefixos conhecidos (`sk-`, `AIza`, `ghp_`, `xox`) + entropia de Shannon (> 4.6 bits) em tokens de 32+ caracteres, em `.py/.js/.json/.md/.env.example/.yml/.yaml`. | Sim |
| **G_QUALIDADE** | `templates/gates/G_QUALIDADE.py` | Compilação (`py_compile`) de todos os `.py` do projeto. Não valida stubs, testes ou UI. | Sim |
| **G_HARNESS_COMPAT** | `templates/gates/G_HARNESS_COMPAT.py` | Nada de fato — é um *stub* que sempre imprime sucesso e retorna `exit 0`. | Sim |
| **G_SEGURANCA** | `scripts/gates/G_SEGURANCA.py` | 7 camadas: headers OWASP, JWT HS256 + tampering + expiração + PBKDF2, varredura estática de SQL Injection, config Nginx (rate limit/TLS/`server_tokens`), hardening Docker (non-root/healthcheck), modo WAL + tabela de auditoria, `securitySchemes` do OpenAPI. | **Não** — é executado manualmente, fora do comando `audit` |

## 3. Lacuna de cobertura mais relevante desta tag
O gate mais robusto tecnicamente (`G_SEGURANCA.py`, 7 camadas, introduzido na v4.2.0 e reforçado na v4.3.0 com os testes de produção) **não está integrado ao fluxo automático** `python scripts/aidd.py audit`. Um projeto pode passar 100% no `audit` padrão e ainda assim nunca ter sido submetido à auditoria de segurança, a menos que o desenvolvedor lembre de rodar o script manualmente.
