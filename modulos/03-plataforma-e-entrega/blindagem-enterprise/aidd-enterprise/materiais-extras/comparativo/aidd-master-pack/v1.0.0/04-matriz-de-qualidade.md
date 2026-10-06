# Matriz Atômica de Qualidade — AIDD Master Pack `v1.0.0`

> **Tag analisada:** `v1.0.0` (commit `729ce3e`)
> Esta matriz documenta **somente** os mecanismos de qualidade que existem de fato no snapshot da tag, camada por camada. Onde um mecanismo citado em versões posteriores do framework não existe aqui, isso é declarado explicitamente em vez de omitido.

---

## 1. Critérios de Qualidade por Camada de Entrega

### A. Camada de Persistência (`database.py`)
- **Concorrência:** SQLite em modo WAL (`PRAGMA journal_mode=WAL;`, `synchronous=NORMAL`). Sem `busy_timeout` explícito e sem `PRAGMA foreign_keys=ON`.
- **Suporte a Postgres:** opcional, só se `psycopg2` estiver instalado no ambiente — sem abstração de adaptador, é um `if/else` dentro de `get_connection()`.
- **Soft-delete / auditoria histórica:** **não existe.** `add_module.py` gera apenas coluna `ativo` (flag booleana), sem coluna de exclusão lógica (`deletado_em`) nem tabela de auditoria.
- **Versionamento de schema:** **não existe.** Não há tabela `_schema_migrations` nem mecanismo de migração — cada `init_schema()` roda `CREATE TABLE IF NOT EXISTS` idempotente, sem controle de versão.
- **Zero SQL Injection:** as queries geradas por `add_module.py` usam parametrização (`?`), mas isso é uma convenção seguida manualmente pelo template, não imposta por um gate ou linter dedicado.
- **Gate validador:** nenhum gate audita especificamente esta camada. `G_QUALIDADE.py` só garante que o arquivo compila.

### B. Camada de Front-End (`src/static/components/*.html`)
- **Padrão visual:** existe uma diretriz em prosa (`templates/rules/03_impeccable.md`) pedindo "Dark Theme com Glassmorphism", tipografia pura e proibição de emojis em UI — mas **não há linter ou gate que verifique isso automaticamente**. É uma instrução para o agente de IA seguir por conta própria.
- **Ícones vetoriais / zero emoji:** regra documentada, sem verificação mecânica.
- **Diálogos nativos (`alert`/`confirm`):** não há regra escrita nem gate proibindo seu uso nesta tag.
- **Acessibilidade (WCAG):** não mencionada em nenhum arquivo de regras ou gate desta tag.
- **Paginação / busca / KPIs:** o componente gerado por `add_module.py` é um card simples (input + botão + container de lista); não há paginação, busca ou métricas.
- **Gate validador:** nenhum.

### C. Camada de Back-End (`services.py`)
- **CRUD:** apenas 3 dos 5 métodos típicos são gerados — `listar()`, `criar()`, `deletar()`. **Não há** `atualizar()` nem `obter_por_id()` no template padrão de `add_module.py`.
- **Result Pattern:** **não existe.** Os métodos retornam dicionários ad-hoc (`{"sucesso": True, ...}`), sem um tipo padronizado `Result.ok`/`Result.fail`.
- **Anti-stubs:** não há varredura automática contra `pass`/`TODO`/`NotImplementedError` — `G_QUALIDADE.py` verifica apenas se o arquivo compila, não seu conteúdo semântico.
- **Emissão de eventos:** presente e real — `criar()` e `deletar()` emitem eventos via `EventBus.emit()`, mas sem UUID de rastreamento nem schema de payload validado.
- **Linter anti-acoplamento:** **não existe.** Nada impede um módulo de importar diretamente de outro (`from modules.produtos.backend.services import ...`), e isso de fato acontece em pelo menos um dos exemplos de referência.
- **Fila de tarefas assíncronas:** **não existe.** O único uso de concorrência é a thread solta do `WebhookDispatcher`.
- **Gate validador:** `G_QUALIDADE.py` (sintaxe apenas).

### D. Camada de Rotas e Contratos de API (`routes.py` / `openapi.py`)
- **Especificação de rotas:** `RouteRegistry` com decorators `@get`/`@post` que aceitam `summary` e `tags` opcionais.
- **OpenAPI gerado:** versão simplificada (`"openapi": "3.0.0"`), sem `body_schema` nem `query_params` estruturados — apenas `summary`, `tags` e uma resposta genérica `200`.
- **Swagger UI:** servida via página HTML que carrega `swagger-ui-dist` de um **CDN externo** (`unpkg.com`) — não funciona offline e depende de conexão com a internet.
- **MCP / JSON-RPC:** **não existe** nesta tag.
- **Snapshot de contrato (hash):** **não existe.** Nada impede uma rota de mudar de assinatura silenciosamente entre gerações.
- **CORS:** depende de implementação manual por projeto (visto em `server.py` dos exemplos), não é padrão do kernel.
- **Gate validador:** nenhum gate audita contratos de rota nesta tag.

### E. Camada de Integração Cross-Domain (`events.py` / `webhooks.py`)
- **Envelope de evento:** **não padronizado.** `EventBus.emit(nome, dados)` aceita qualquer payload; não há `event_id`, `timestamp` ou `origin_module` obrigatórios.
- **Isolamento de erros:** parcial — `EventBus.emit()` captura exceção por listener individualmente (um listener quebrado não derruba os demais), o que é um acerto real desta versão.
- **Webhooks assinados (HMAC):** **não existe.** `WebhookDispatcher` envia o payload em texto puro, sem cabeçalho de assinatura, sem verificação de integridade no destino.
- **Retry / fila morta:** **não existe.** Falha de entrega apenas gera um `print` de aviso no console; não há nova tentativa nem persistência do evento falho.
- **Gate validador:** nenhum.

### F. Camada de Governança, Contexto e Testabilidade (`tests/`, regras, manifesto)
- **Especificação formal (SPEC em níveis):** **não existe.** Não há `SPEC-ARQUITETURA.md` nem processo de aprovação de escopo antes da geração de código.
- **Sincronização multi-IDE:** **não existe automaticamente.** Nos exemplos de referência, arquivos como `AGENTS.md`, `CLAUDE.md`, `GEMINI.md` e `.cursorrules` aparecem com conteúdo idêntico copiado manualmente — não há um gerador único que os sincronize.
- **Grafo de memória do projeto:** **não existe** (`CONTEXTO-PROJETO.md` ou equivalente não está presente em nenhum exemplo).
- **Templates de subagentes por papel:** **não existem** nesta tag.
- **Cobertura de teste:** o teste gerado automaticamente cobre apenas criar/listar/deletar do módulo recém-criado — não há garantia de cobertura ampla, nem verificação de mutação de estado além do que o template já embute.
- **Benchmark de concorrência:** **não existe** (`aidd.py bench` não existe como comando).
- **Auto-remediação:** **não existe** (`aidd.py heal` não existe como comando).
- **Relatório estruturado de auditoria:** **não existe.** `audit` imprime mensagens de texto simples no console (`[OK]`/`[FAIL]`); não gera nenhum arquivo `RELATORIO-*.json`.
- **Gate validador:** `G_QUALIDADE.py`, `G_SEGREDOS.py`, `G_HARNESS_COMPAT.py` (ver tabela abaixo).

---

## 2. Tabela Consolidada dos 3 Gates Mecânicos

| Gate | O que audita de fato | Condição de bloqueio | Observação honesta |
| :--- | :--- | :--- | :--- |
| **1. G_SEGREDOS** | Regex contra 4 prefixos de chave conhecidos (`sk-`, `AIza`, `ghp_`, `xox`) + entropia de Shannon (> 4.6 bits) em tokens de 32+ caracteres. | Qualquer padrão suspeito encontrado em arquivos `.py/.js/.json/.md/.env.example/.yml/.yaml`. | Heurístico simples: gera falsos positivos (hashes de teste, UUIDs) e pode não detectar segredos de baixa entropia. |
| **2. G_QUALIDADE** | `py_compile` recursivo em todo `.py` do projeto (fora de `.git`, `node_modules`, `.venv`). | Qualquer erro de sintaxe Python. | **Não roda os testes `pytest`**, não faz lint de estilo, não audita UI ou acessibilidade — apenas garante que o código compila. |
| **3. G_HARNESS_COMPAT** | Nada. O corpo da função é um `print` de sucesso seguido de `sys.exit(0)`. | Nunca falha. | É um gate de fachada — presente na CLI e na cadeia de `audit`, mas sem lógica de verificação real. |

**Gates que existem em versões posteriores do framework e não existem em `v1.0.0`:** `G_ESTRUTURA` (validação de layout/anti-acoplamento), `G_TESTES` (execução obrigatória de pytest dentro da auditoria), `G_CONTRACTS` (validação/snapshot de OpenAPI e MCP), `G_SEGURANCA` (auditoria OWASP multi-camada).

---

## 3. Leitura honesta do conjunto

Dos 3 gates existentes, apenas 2 fazem verificação real (`G_SEGREDOS` e `G_QUALIDADE`); o terceiro é decorativo. Nenhum gate impõe execução de testes, cobertura, contratos de API ou padrões de UI — essas responsabilidades ficam inteiramente a cargo da disciplina do agente de IA ou do desenvolvedor humano seguindo as diretrizes em prosa de `templates/rules/`. `v1.0.0` oferece uma **rede de segurança mínima e determinística** (sintaxe válida + ausência de segredos óbvios), não uma auditoria de qualidade abrangente.
