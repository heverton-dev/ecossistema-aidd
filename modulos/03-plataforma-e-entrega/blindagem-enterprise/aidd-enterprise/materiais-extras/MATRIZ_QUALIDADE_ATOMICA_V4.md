# Matriz Atômica de Qualidade do AIDD Master Pack v5.1 (Nível Ultra — 12 Pilares Formação.DEV)

## 1. Critérios de Qualidade por Camada de Entrega

### A. Camada de Persistência & Banco de Dados (`models.py` / `database.py`)
- **Concorrência Segura:** SQLite inicializado em modo WAL (`PRAGMA journal_mode=WAL;`), `synchronous=NORMAL` e `busy_timeout=5000`.
- **Integridade Relacional & Soft-Delete:** `PRAGMA foreign_keys=ON;` e suporte nativo a exclusão lógica via coluna `deletado_em` (auditoria histórica).
- **Zero SQL Injection:** 100% das queries utilizam parametrização com placeholders (`?` ou `%s`). Interpolação de strings é proibida.
- **Zero Connection Leak:** Uso obrigatório de context manager (`with db.get_connection()`) auditado estaticamente pelo linter do `G_ESTRUTURA`.
- **Seed Fixtures Determinísticas:** A função `init_schema()` popula automaticamente 2 registros de exemplo se a tabela estiver vazia.
- **Versionamento de Schema:** Tabela interna `_schema_migrations` registrando versões de schema aplicadas por módulo.
- **Gate Validador:** `G_ESTRUTURA`, `G_TESTES` e `G_SEGURANCA`.

---

### B. Camada de Front-End & Design System (`components/*.html` / `Impeccable UI`)
- **Padrão Impeccable UI:** Layout responsivo em Tailwind CSS com paleta Slate/Indigo, bordas sutis (`border-slate-800`), sombras de elevação e cantos arredondados (`rounded-xl`).
- **Zero Emojis & Ícones Vetoriais:** Proibição de emojis como ícones funcionais. Uso exclusivo de SVGs Lucide vetoriais escaláveis.
- **Zero Diálogos Nativos de SO:** Proibição de `alert()`, `confirm()` ou `prompt()`. Uso obrigatório de Modais HTML customizados e Toasts assíncronos de feedback.
- **Acessibilidade WCAG 2.1:** Botões com `type="button"`, `aria-label`, foco acessível e labels semânticos auditados pelo `G_QUALIDADE`.
- **Tabela Paginada com Busca:** Paginação dinâmica (`pagina`, `limite`, `busca`) e contador de registros.
- **Cards de KPIs no Topo:** Indicadores de negócio consolidados (`obter_metricas()`) para visibilidade executiva instantânea.
- **Gate Validador:** `G_ESTRUTURA` e `G_QUALIDADE`.

---

### C. Camada de Back-End & Regras de Negócio (`services.py` / `result.py`)
- **Full CRUD Diligente:** Toda entidade implementa 5 métodos reais: `listar()`, `obter_por_id()`, `criar()`, `atualizar()`, `deletar()`, mais `obter_metricas()`.
- **Padrão Resultado Monádico (`Result Pattern`):** Retornos padronizados com `Result.ok(valor)` ou `Result.fail(erro, codigo)` eliminando falhas 500 não tratadas.
- **Anti-Stubs & Anti-Pass:** Proibição estrita de marcadores vazios (`pass`, `...`, `NotImplementedError`, `TODO`). Todo código é compilável e funcional.
- **Desacoplamento HTTP:** O serviço não recebe objetos HTTP (`request`, `headers`); recebe apenas dicionários ou tipos primitivos tipados.
- **Emissão de Eventos:** Toda mutação de estado (`criar`, `atualizar`, `deletar`) emite um evento no `EventBus` pub/sub com rastreabilidade UUID.
- **Linter AST Anti-Acoplamento:** Proibição de imports diretos entre módulos irmãos (`modules.crm` -> `modules.erp`), forçando o uso do `EventBus`.
- **Fila de Tarefas Assíncronas (`JobQueue`):** Processamento em background sem bloqueio do servidor HTTP (`src/core/jobs.py`).
- **Gate Validador:** `G_ESTRUTURA`, `G_QUALIDADE`, `G_TESTES` e `G_CONTRACTS`.

---

### D. Camada de Rotas & Contratos de API (`routes.py` / `openapi.py`)
- **OpenAPI 3.1 Dinâmico:** Todas as rotas são declaradas via `@registry.get` e `@registry.post` com `summary`, `tags`, `body_schema`, `query_params` e `responses`.
- **Swagger Studio Vivo:** Interface Swagger UI em `/docs` que permite execução interativa das rotas diretamente pelo navegador.
- **Universal MCP JSON-RPC 2.0:** O servidor `/mcp` expõe ferramentas dinâmicas para cada módulo (`mod_<modulo>_listar`, `mod_<modulo>_criar`, etc.) com inputSchema validado.
- **Snapshot SHA-256 de Contratos:** Geração e verificação de hash SHA-256 no `G_CONTRACTS` para prevenir quebras acidentais de contrato.
- **CORS Preflight Middleware:** Resposta automática a requisições `OPTIONS` com headers `Access-Control-Allow-Origin: *`.
- **Gate Validador:** `G_CONTRACTS` e `G_HARNESS_COMPAT`.

---

### E. Camada de Integração Cross-Domain (`events.py` / `webhooks.py`)
- **Envelope Padronizado:** Cada evento transita com: `event_id` (UUID), `event_name`, `timestamp` (ISO UTC), `origin_module` e `data`.
- **Isolamento de Erros:** Falha em um listener de evento não interrompe a execução do serviço principal.
- **Webhooks com HMAC SHA-256:** Disparos externos assíncronos assinados criptograficamente no cabeçalho `X-Hub-Signature-256`.
- **Gate Validador:** `G_TESTES` e `G_SEGURANCA`.

---

### F. Camada de Governança, Contexto & Testabilidade (`tests/unit/` / `CONTEXTO-PROJETO.md`)
- **SPEC em 3 Níveis Estruturados:** `SPEC-ARQUITETURA.md` com seções segregadas: Negócio, Backend e Frontend.
- **Sincronização Multi-IDE:** Geração automática de regras para `.cursor/rules/`, `.claude/` e `.agent/rules/`.
- **Grafo de Memória (`CONTEXTO-PROJETO.md`):** Mapa de entidades e contratos permitindo reinício de sessão da IA com 500 tokens.
- **Templates de Subagentes por Papel:** `agent_architect`, `agent_backend`, `agent_frontend`, `agent_qa`.
- **Cobertura 100% com Testes de Mutação:** `tests/unit/test_<modulo>.py` com validação de mutação de estado (`assert item_antes != item_depois`).
- **Benchmark Concorrente (`aidd bench`):** Teste de 100 requisições simultâneas garantindo latência média < 2ms e zero lock contention.
- **Auto-Remediação (`aidd heal`):** Recuperação determinística de templates e manifestos corrompidos.
- **Auditoria Factual:** Geração do relatório `RELATORIO-AUDITORIA.json` contendo métricas reais (duração em ms, status dos 7 gates, nota de segurança).
- **Gate Validador:** `G_TESTES`, `G_ESTRUTURA`, `G_QUALIDADE`, `G_CONTRACTS`, `G_SEGREDOS`, `G_HARNESS_COMPAT`, `G_SEGURANCA`.

---

## 2. Tabela Consolidada dos 7 Quality Gates Mecânicos

| Gate | O que Audita no Código Real | Condição de Bloqueio |
| :--- | :--- | :--- |
| **1. G_ESTRUTURA** | Fatias em `src/modules`, layout, AST Anti-Acoplamento e Scanner de Conexões Abertas. | Falta de fatias, import direto entre módulos ou connection leaks. |
| **2. G_QUALIDADE** | Compilação `py_compile`, varredura AST anti-stubs e Linter Impeccable UI / WCAG 2.1. | Erro de sintaxe, stubs vazios (`pass`) ou diálogos nativos de SO (`alert`). |
| **3. G_TESTES** | Execução real com `pytest` em `tests/unit/`, asserções de mutação e healthcheck. | Qualquer teste FAILED ou 0 testes encontrados. |
| **4. G_CONTRACTS** | Conformidade `RouteRegistry`, OpenAPI 3.1, MCP Server e Snapshot SHA-256. | Violação de contrato, schema JSON inválido ou quebra de snapshot. |
| **5. G_SEGREDOS** | Entropia de Shannon ($H > 4.75$) e Regex contra chaves. | Chave de API, segredo ou token hardcoded. |
| **6. G_HARNESS_COMPAT** | Zero API Key e compatibilidade CLI/SO multiplataforma. | Dependência externa paga ou comando quebrado. |
| **7. G_SEGURANCA** | 7 Camadas: OWASP, JWT HS256, Zero SQLi, SQLite WAL, Docker Non-Root, Nginx Shield, etc. | Qualquer vulnerabilidade detectada (Score < 100%). |
