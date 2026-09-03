# Matriz Atômica de Qualidade por Camada de Entrega — AIDD Master Pack v4.1.0

> **Tag documentada:** `v4.1.0` (commit `1daf757`, 31/08/2026)
> Esta matriz cobre **apenas** os mecanismos de qualidade presentes no snapshot desta tag. A tag `v4.1.0` possui **3 gates mecânicos** (`G_QUALIDADE`, `G_SEGREDOS`, `G_HARNESS_COMPAT`), ao contrário de versões posteriores (v5.x) que chegam a 7 gates (`G_ESTRUTURA`, `G_TESTES`, `G_CONTRACTS`, `G_SEGURANCA`, etc.). Nenhum desses 4 gates adicionais existe no código desta tag e por isso não são citados como validadores abaixo.

---

## A. Camada de Persistência (`database.py` / `models.py`)

- **Concorrência:** SQLite aberto com `PRAGMA journal_mode=WAL;` e `PRAGMA synchronous=NORMAL;` (`templates/v2/database.py`). Não há `busy_timeout` configurado via PRAGMA (apenas o timeout de conexão do driver Python, `sqlite3.connect(db_path, timeout=10.0)`).
- **Dual-backend real:** se `DATABASE_URL` iniciar com `postgres://`/`postgresql://`, tenta usar `psycopg2` com `RealDictCursor`; caso contrário, usa SQLite. Não há camada de abstração/ORM — é seleção condicional simples.
- **Módulos gerados por `add_module.py`:** schema com `id`, `titulo`, `dados_json` (JSON serializado como texto), `ativo` (flag de soft-visibilidade, não soft-delete real), `criado_em`. Índice em `ativo`.
- **Sem soft-delete real, sem versionamento de schema, sem seed fixtures automáticas** — nenhum desses mecanismos existe nesta tag (aparecem apenas em versões v5.x).
- **Zero SQL Injection:** todas as queries observadas usam parametrização (`?` / `%s`), inclusive no código gerado por `add_module.py`.
- **Gate validador real:** `G_QUALIDADE.py` (apenas compila a sintaxe do `.py`, não valida schema nem PRAGMAs).

## B. Camada de Front-End (`src/static/*.html`, `templates/rules/03_impeccable.md`)

- **Padrão "Impeccable" documentado (não auto-verificado por gate):** zero emojis, ícones SVG (Lucide/Heroicons), header de linha única (`white-space: nowrap`, `overflow-x: auto`), scrollbars de 4px, botões `inline-flex` sem quebra de texto.
- **Feedback tátil via `templates/v2/shared/ui/feedback.py` e `feedback.js`:** motor de Toasts/Modais para substituir `alert()`/`confirm()` nativos — presente como shared kernel, copiado por `compose_suite.py` e `provision_project.py`.
- **Nenhum gate mecânico valida acessibilidade, ausência de emojis, ou conformidade de scrollbar nesta tag.** A conformidade com o padrão Impeccable depende inteiramente da disciplina do agente/desenvolvedor ao escrever o HTML — não há linter automatizado (`G_QUALIDADE.py` só verifica sintaxe Python, não HTML/CSS/JS).
- **Componentes gerados por `add_module.py`** são cards HTML simples com input + botão "Adicionar", sem paginação, busca ou KPIs.

## C. Camada de Back-End & Regras de Negócio (`services.py`)

- **CRUD gerado automaticamente é, na prática, CRD:** `add_module.py` produz `listar()`, `criar()`, `deletar()`. **Não gera `atualizar()`** nem rota de update — divergência real frente ao discurso de "Full CRUD Diligente em 100% dos Módulos" do `SKILL.md`.
- **Sem Result Pattern:** métodos retornam dicionários simples (`{"sucesso": True, ...}`), sem um tipo padronizado de erro/sucesso monádico.
- **Emissão de eventos:** `criar()` e `deletar()` emitem eventos via `EventBus.emit()` quando uma instância de `events` é injetada no serviço — mecanismo real e testado (o teste unitário gerado verifica isso).
- **Desacoplamento HTTP:** os serviços recebem tipos primitivos (`str`, `dict`, `int`), não objetos de request — correto.
- **Sem linter anti-acoplamento entre módulos:** nada nesta tag impede um módulo de importar diretamente código de outro módulo irmão; a separação por EventBus é uma convenção documental (`templates/rules/04_cross_project.md`), não uma regra imposta por gate.
- **Gate validador real:** `G_QUALIDADE.py` e, indiretamente, `G_SEGREDOS.py` (varre `.py` também).

## D. Camada de Rotas & Contratos de API (`routes.py` / `openapi.py`)

- **`RouteRegistry` real:** suporta `GET`, `POST`, `PUT`, `DELETE`, `PATCH`, com decoradores `@registry.get(...)` / `@registry.post(...)` aceitando `summary`, schemas de resposta e normalização de respostas de erro (`templates/v2/openapi.py`, ~1000 linhas incluindo geração de UI Swagger).
- **Swagger Studio em `/docs`:** citado consistentemente em README/SKILL/exemplos como rota funcional, com testador interativo.
- **Servidor MCP (`/mcp`) presente nos exemplos mais completos** (`enterprise-suite-v4`, `logistica-hub-v4`), mas implementado como classe **hardcoded manualmente por domínio** (ex.: `LogisticaMCPServer` com dezenas de `tools` descritos à mão), e **não gerado automaticamente** a partir do `RouteRegistry` por nenhum script desta tag.
- **Rotas geradas por `add_module.py`** não incluem `PUT`/`PATCH` apesar do `RouteRegistry` suportar esses verbos — outra evidência da lacuna de "Update" no CRUD automático.
- **Sem snapshot de contrato (SHA-256) e sem gate `G_CONTRACTS`** — mecanismos inexistentes nesta tag.
- **Gate validador real:** nenhum gate desta tag valida especificamente contratos OpenAPI/MCP; `G_QUALIDADE.py` só garante que o `.py` compila.

## E. Camada de Integração Cross-Domain (`events.py` / `webhooks.py`)

- **EventBus real, porém síncrono e em memória:** `templates/v2/events.py` é um `defaultdict(list)` de handlers chamados sequencialmente dentro do próprio processo/requisição. Isolamento de erro por listener (`try/except` por handler) está implementado — uma falha em um listener não derruba os demais.
- **Sem envelope padronizado de evento** (não há `event_id`/UUID, `timestamp` ISO ou `origin_module` no payload emitido por `add_module.py`; o evento carrega apenas os dados brutos passados por quem chamou `emit()`).
- **Webhooks disparados em thread separada** (`threading.Thread(daemon=True)`), evitando bloquear a resposta HTTP — mecanismo real.
- **Webhooks SEM assinatura HMAC**, apesar de a documentação (`README.md`, `SKILL.md`, `templates/rules/04_cross_project.md`) afirmar "Disparo assíncrono com assinatura HMAC para cada evento de domínio". O código de `templates/v2/webhooks.py` envia apenas `Content-Type: application/json` e um `User-Agent` customizado — nenhum cabeçalho de assinatura.
- **Gate validador real:** nenhum. Não há teste automático de entrega de webhook nem verificação de assinatura (porque ela não existe).

## F. Camada de Governança, Segurança & Produção (novidade desta tag)

- **Autenticação JWT HS256 artesanal** (`templates/v2/security.py`): encode/decode Base64URL manual, verificação de assinatura com `hmac.compare_digest` (comparação em tempo constante — correto), checagem de expiração (`exp`). **Sem suporte a refresh token, sem revogação/blacklist.**
- **Hash de senha PBKDF2-HMAC-SHA256** com 100.000 iterações e salt aleatório de 16 bytes — implementação correta.
- **Modo `ALLOW_ANONYMOUS=1`** permite bypass total de autenticação para desenvolvimento — presente e documentado no `Dockerfile` (`ALLOW_ANONYMOUS=0` por padrão em produção).
- **Segredo JWT com fallback hardcoded** no próprio código-fonte (`security.py`) e valor literal em texto plano dentro do `docker-compose.yml` de exemplo — risco real de vazamento se o operador não sobrescrever a env var.
- **Nginx de produção:** TLS 1.2/1.3, HTTP/2, rate limiting 100 req/s por IP com burst 50, limite de 100 conexões simultâneas por IP, headers OWASP (`X-Frame-Options`, `HSTS`, etc.), compressão gzip, cache de estáticos — tecnicamente sólido para um único nó.
- **Certificado SSL autoassinado por padrão**, sem automação real de Let's Encrypt (o `nginx.conf` referencia o desafio ACME, mas nenhum script desta tag executa `certbot`). Existe um *fallback* de certificado dummy caso o OpenSSL falhe, sem alerta destacado.
- **Docker não-root:** usuário dedicado `aidduser` (UID 10001), princípio de menor privilégio OWASP aplicado corretamente.
- **Gate validador real:** `G_SEGREDOS.py` (entropia de Shannon + regex de prefixos conhecidos) é o único gate desta camada; `G_HARNESS_COMPAT.py` não faz nenhuma checagem de segurança (é um stub).

---

## 2. Tabela Consolidada dos 3 Gates Mecânicos Reais desta Tag

| Gate | O que audita de fato no código desta tag | Condição de bloqueio | É funcional? |
| :--- | :--- | :--- | :---: |
| **G_QUALIDADE** | Roda `python -m py_compile` em todo arquivo `.py` do projeto (ignorando `.git`, `node_modules`, `.venv`). | Qualquer erro de sintaxe Python. | Sim |
| **G_SEGREDOS** | Regex contra prefixos de chave conhecidos (`sk-`, `AIza`, `ghp_`, `xox[baprs]-`) + cálculo de entropia de Shannon (limiar > 4.6 bits) em tokens de 32+ caracteres, varrendo `.py .js .json .md .env.example .yml .yaml`. | Qualquer padrão suspeito ou string de alta entropia. | Sim |
| **G_HARNESS_COMPAT** | Nada. Imprime uma mensagem fixa de sucesso e sai com código 0. | Nunca bloqueia. | Não (stub) |

**Execução:** `python scripts/aidd.py audit` roda os 3 gates em sequência e interrompe no primeiro `exit != 0`. Não há gate de estrutura de camadas, gate de execução de testes (`pytest` só roda via `aidd.py test`, fora do `audit`), gate de contratos de API, nem gate consolidado de segurança de infraestrutura — esses só aparecem em tags posteriores.
