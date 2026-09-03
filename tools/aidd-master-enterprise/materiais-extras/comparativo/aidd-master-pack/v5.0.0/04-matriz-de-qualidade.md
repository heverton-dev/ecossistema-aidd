# Matriz Atômica de Qualidade por Camada de Entrega — AIDD Master Pack

> **Tag/versão documentada:** `v5.0.0`
> **Fonte primária:** `MATRIZ_QUALIDADE_ATOMICA_V4.md` (versionado dentro desta tag), cruzado com `scripts/gates/*.py` extraídos via `git archive v5.0.0`.
> **Escopo:** somente os gates e mecanismos de qualidade que existem de fato no código desta tag. Recursos que aparecem apenas em `v5.1.0` ou em tags posteriores (ex.: validação de CSS offline-first no `G_CONTRACTS`, checagens de portal 4-em-1) **não** estão incluídos aqui.

---

## Os 7 Quality Gates mecânicos desta tag

Confirmados em `scripts/gates/`: `G_CONTRACTS.py`, `G_ESTRUTURA.py`, `G_HARNESS_COMPAT.py`, `G_QUALIDADE.py`, `G_SEGREDOS.py`, `G_SEGURANCA.py`, `G_TESTES.py`. Todos são invocados como subprocessos isolados por `aidd.py audit` (`python <gate>.py --dir <alvo>`) e precisam retornar exit code 0 para a homologação ser concedida.

| Gate | O que audita no código real | Condição de bloqueio |
| :--- | :--- | :--- |
| **G_ESTRUTURA** | Layout de fatias em `src/modules/`, linter AST anti-acoplamento entre módulos irmãos, scanner de vazamento de conexão de banco. | Falta de fatia vertical, import direto entre módulos ou conexão aberta sem `with`. |
| **G_QUALIDADE** | Compilação `py_compile`, varredura AST anti-stubs (`pass`, `...`, `NotImplementedError`, `TODO`), linter Impeccable UI / WCAG 2.1. | Erro de sintaxe, stub vazio ou diálogo nativo de SO (`alert`/`confirm`/`prompt`). |
| **G_TESTES** | Execução real de `pytest` em `tests/unit/`, asserções de mutação de estado, healthcheck. | Qualquer teste `FAILED` ou zero testes encontrados. |
| **G_CONTRACTS** | Conformidade do `RouteRegistry`, especificação OpenAPI 3.1, servidor MCP e snapshot SHA-256 de contratos. | Violação de contrato, schema JSON inválido ou quebra de snapshot. |
| **G_SEGREDOS** | Entropia de Shannon (H > 4.75) e regex contra padrões de chave/API key hardcoded. | Qualquer segredo ou token detectado no código. |
| **G_HARNESS_COMPAT** | Ausência de API key obrigatória e compatibilidade de CLI/SO multiplataforma. | Dependência externa paga ou comando quebrado em algum harness suportado. |
| **G_SEGURANCA** | 7 camadas: headers OWASP, criptografia JWT HS256, varredura estática anti-SQLi, varredura de segredos, config Nginx (rate limiting/SSL/anti-DDoS), Docker non-root, SQLite WAL + logs de auditoria. | Qualquer vulnerabilidade detectada (nota abaixo de 100%). |

---

## A. Camada de Persistência & Banco de Dados (`models.py` / `database.py`)

- **Concorrência segura:** SQLite inicializado em modo WAL (`PRAGMA journal_mode=WAL`), `synchronous=NORMAL`, `busy_timeout=5000`.
- **Integridade relacional & soft-delete:** `PRAGMA foreign_keys=ON` e coluna `deletado_em` para exclusão lógica com auditoria histórica.
- **Zero SQL Injection:** 100% das queries parametrizadas (`?`/`%s`); interpolação de string proibida.
- **Zero connection leak:** uso obrigatório de context manager (`with db.get_connection()`), auditado estaticamente pelo `G_ESTRUTURA`.
- **Seed fixtures determinísticas:** `init_schema()` popula 2 registros de exemplo se a tabela estiver vazia.
- **Versionamento de schema:** tabela interna `_schema_migrations`.
- **Gates validadores:** `G_ESTRUTURA`, `G_TESTES`, `G_SEGURANCA`.

---

## B. Camada de Front-End & Design System (`components/*.html` / Impeccable UI)

- **Padrão Impeccable UI:** Tailwind CSS, paleta Slate/Indigo, bordas sutis, sombras de elevação, cantos arredondados.
- **Zero emojis & ícones vetoriais:** proibição de emoji como ícone funcional; uso exclusivo de SVG Lucide.
- **Zero diálogos nativos de SO:** proibição de `alert()`/`confirm()`/`prompt()`; modais HTML customizados e toasts assíncronos.
- **Acessibilidade WCAG 2.1:** `type="button"`, `aria-label`, foco acessível, labels semânticos — auditado pelo `G_QUALIDADE`.
- **Tabela paginada com busca:** paginação dinâmica (`pagina`, `limite`, `busca`) e contador de registros.
- **Cards de KPIs no topo:** indicadores agregados via `obter_metricas()`.
- **Gates validadores:** `G_ESTRUTURA`, `G_QUALIDADE`.

---

## C. Camada de Back-End & Regras de Negócio (`services.py` / `result.py`)

- **Full CRUD diligente:** todo módulo implementa `listar()`, `obter_por_id()`, `criar()`, `atualizar()`, `deletar()` e `obter_metricas()`.
- **Padrão Resultado Monádico:** retornos padronizados `Result.ok(valor)` / `Result.fail(erro, codigo)`, eliminando exceções soltas e falhas 500 não tratadas.
- **Anti-stubs & anti-pass:** proibição de marcadores vazios; todo código deve ser compilável e funcional.
- **Desacoplamento HTTP:** serviços recebem apenas dicionários/tipos primitivos, nunca objetos `request`/`headers` crus.
- **Emissão de eventos:** toda mutação (`criar`/`atualizar`/`deletar`) publica no `EventBus` com rastreabilidade UUID.
- **Linter AST anti-acoplamento:** proíbe import direto entre módulos irmãos, forçando comunicação via `EventBus`.
- **Fila de tarefas assíncronas:** `JobQueue` em `src/core/jobs.py` processa tarefas em background sem bloquear o HTTP.
- **Gates validadores:** `G_ESTRUTURA`, `G_QUALIDADE`, `G_TESTES`, `G_CONTRACTS`.

---

## D. Camada de Rotas & Contratos de API (`routes.py` / `openapi.py`)

- **OpenAPI 3.1 dinâmico:** rotas declaradas via `@registry.get`/`@registry.post` com `summary`, `tags`, `body_schema`, `query_params` e `responses`.
- **Swagger Studio vivo:** interface em `/docs` com execução interativa de rotas no navegador.
- **MCP universal JSON-RPC 2.0:** `/mcp` expõe ferramentas dinâmicas por módulo (`mod_<modulo>_listar`, `mod_<modulo>_criar` etc.) com `inputSchema` validado.
- **Snapshot SHA-256 de contratos:** hash gerado e verificado pelo `G_CONTRACTS` para prevenir quebras acidentais.
- **CORS preflight middleware:** resposta automática a requisições `OPTIONS` com `Access-Control-Allow-Origin: *`.
- **Gates validadores:** `G_CONTRACTS`, `G_HARNESS_COMPAT`.

---

## E. Camada de Integração Cross-Domain (`events.py` / `webhooks.py`)

- **Envelope padronizado:** todo evento carrega `event_id` (UUID), `event_name`, `timestamp` (ISO UTC), `origin_module` e `data`.
- **Isolamento de erros:** falha em um listener não interrompe o serviço principal (cada handler é chamado dentro de um `try/except` isolado).
- **Webhooks com HMAC SHA-256:** disparo assíncrono assinado no cabeçalho `X-Hub-Signature-256`, com retry.
- **Driver plugável (opt-in):** `InMemoryEventBusDriver` por padrão; `RedisStreamsDriver` disponível via `EVENTBUS_URL` para distribuir eventos entre instâncias — mas isso é uma capacidade presente no código, não um gate específico que a valide isoladamente.
- **Gates validadores:** `G_TESTES`, `G_SEGURANCA`.

---

## F. Camada de Governança, Contexto & Testabilidade (`tests/unit/` / `CONTEXTO-PROJETO.md`)

- **SPEC em 3 níveis:** `SPEC-ARQUITETURA.md` segregado em Negócio, Back-end e Front-end.
- **Sincronização multi-IDE:** geração automática de regras para `.cursor/rules/`, `.claude/` e `.agent/rules/`.
- **Grafo de memória:** `CONTEXTO-PROJETO.md` mapeia entidades e contratos para retomar sessões de IA com baixo custo de tokens.
- **Templates de subagentes por papel:** `agent_architect`, `agent_backend`, `agent_frontend`, `agent_qa` (e `agent_domain_refiner`, usado pelo fluxo `refine-module`).
- **Cobertura com testes de mutação:** `tests/unit/test_<modulo>.py` valida `assert item_antes != item_depois`.
- **Benchmark de concorrência:** `aidd bench` mede latência e RPS sob carga concorrente no SQLite WAL.
- **Auto-remediação:** `aidd heal` recompõe módulos e manifestos a partir do plano salvo.
- **Auditoria factual:** `RELATORIO-AUDITORIA.json` com duração em ms, status por gate e status geral (`APROVADO`/`REPROVADO`).
- **Gates validadores:** todos os 7 (`G_TESTES`, `G_ESTRUTURA`, `G_QUALIDADE`, `G_CONTRACTS`, `G_SEGREDOS`, `G_HARNESS_COMPAT`, `G_SEGURANCA`).

---

## Nota de escopo importante

Os mecanismos de qualidade acima cobrem apenas o comportamento **padrão** de um projeto composto por esta tag (SQLite WAL, EventBus em memória, JWT local). Componentes opcionais presentes no código desta mesma tag — `PostgresAdapter`, `RedisStreamsDriver`, `OIDCService`, `JobQueue` persistente com DLQ, métricas Prometheus e scaffolding de Terraform/Helm — **não possuem gate dedicado próprio** nesta versão; sua validação ocorre via testes unitários específicos (`tests/unit/test_database_adapter.py`, `test_events_driver.py`, `test_oidc_sso.py`, `test_jobs_queue.py`, `test_metrics.py`, `test_scaffold_infra.py`) executados por `pytest`, não pelos 7 gates de `aidd audit`. Ver `analise-tecnica.md` para o detalhamento desses componentes.

---

*Matriz reconstruída a partir de `MATRIZ_QUALIDADE_ATOMICA_V4.md` desta tag e verificada contra os arquivos reais de `scripts/gates/` extraídos de `git archive v5.0.0`.*
