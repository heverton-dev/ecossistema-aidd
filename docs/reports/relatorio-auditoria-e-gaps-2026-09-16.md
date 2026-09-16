# Relatório de Arquitetura, Engenharia, Modularidade e Auditoria do Ecossistema AIDD

> **Data:** 2026-09-16  
> **Status da Auditoria Global:** REPROVADO (Exit Code 1) — Falha em `G_TESTES_REAIS`  
> **Escopo:** Análise das 5 Camadas Universais, Modularidade (Vertical Slice), Avaliação das 7 Ferramentas e Diagnóstico do Repositório.

---

## 1. Contexto & Conceito: As 5 Camadas Universais do Software

Em engenharia de software canônica, qualquer sistema computacional divide-se em 5 camadas fundamentais mais uma transversal:

| Camada | Função Primária | Manifestação no Ecossistema | Manifestação nas Entregas |
| :--- | :--- | :--- | :--- |
| **1. Entrada (Presentation / Delivery)** | Coleta de estímulos externos e parsing de entrada. | CLI unificada (`ecossistema.py`) e CLIs locais (`application/commands/`). | Rotas HTTP/REST (FastAPI/Flask), DTOs tipados (Pydantic/Zod), Frontend Next.js. |
| **2. Aplicação (Use Cases / Orchestration)** | Orquestra casos de uso e fluxo de trabalho. | Handlers de comando (`cmd_add_module`, `cmd_inject`, `cmd_bench`). | Application Services, Handlers de comando e orquestradores de transação. |
| **3. Domínio (Core / Domain Logic)** | Invariantes de negócio e cálculos puros. | Quality Gates (AST Linters, regras de Bounded Context, BDD specs). | Entidades de domínio, Result Monad (`Result.ok`/`Result.fail`), regras puras. |
| **4. Persistência (Storage / State)** | Sobrevivência de estado no tempo. | Arquivos JSON de plano/auditoria, SQLite (`app.db`), manifests. | `DatabaseAdapter` poliglota (SQLite WAL, PostgreSQL com pooling, Supabase RLS). |
| **5. Infraestrutura & Plataforma** | Conexão com SO, rede, containers e provedores. | Chamadas de subprocess, Git, Docker, Hadolint, MCPs. | Docker Compose, manifests OCI, Cloudflare Workers, serviços externos. |
| **Transversal (Cross-Cutting)** | Segurança, telemetria e resiliência ponta a ponta. | Assinaturas Ed25519/SHA-256 (`aidd-enterprise`), Linters AST. | OpenTelemetry (Tracing ponta a ponta), Circuit Breaker, Rate Limiting, RBAC. |

---

## 2. Diagnóstico das 7 Ferramentas do Ecossistema

O diretório `tools/` abriga 7 subsistemas isolados:

1. **`aidd-master`:** Orquestrador de fatias verticais (Vertical Slice) e monólito modular. Possui as 5 camadas 100% completas em `src/core/`.
2. **`aidd-enterprise`:** Responsável por segurança e resiliência transversal auditada com validação criptográfica (SHA-256).
3. **`aidd-forge`:** Fundação, bootstrap e environment shielding (regras de compliance, templates e hooks).
4. **`aidd-generator`:** Pipeline determinístico de 8 fases para geração de código de software.
5. **`aidd-ops`:** Meta-orquestrador de infraestrutura, cloud, containers e deployment sem vendor lock-in.
6. **`aidd-factory`:** Gerador de integrações e aplicações multi-serviço (orientado a scripts/templates).
7. **`aidd-bridge`:** Empacotador de aplicações low-code para VPS e PostgreSQL.

---

## 3. Matriz de Gaps Identificados

### A. Gaps no Próprio Ecossistema
* **Roteamento Desatualizado na Raiz:** O despachante `ecossistema.py` referenciava apenas 5 ferramentas no help/core, deixando `aidd-factory` e `aidd-bridge` operando como subsistemas desconectados da CLI unificada.
* **Falta de Pipeline Chaining Declarativo:** Inexistência de um fluxo ponta a ponta único (`ecossistema pipeline run --spec spec.json`). O fluxo atual requer acionamento manual de cada ferramenta em sequência.
* **Ausência de Transacionalidade / Rollback (Saga):** Em caso de falha durante a injeção ou geração de código, não há rollback atômico automático de arquivos gerados parcialmente.
* **Dispersão de Persistência:** Logs, relatórios e planos persistem em múltiplos formatos e locais (`docs/planos/`, `audit_reports/`, `PLANO-*.json`, `app.db`).

### B. Gaps nas Entregas Geradas
* **Monocultura de AST (Python Only):** Os linters que garantem Clean Architecture e Bounded Context (`G_AST_BOUNDED_CONTEXT.py`, `G_ARQUITETURA_DELIVERABLE.py`) dependem do módulo `ast` do Python. Entregas em TypeScript/Node, Go ou Rust não possuem linter AST nativo de arquitetura.
* **Falta de Enforcement no Frontend:** O frontend gerado (`export_frontend.py`) não possui gates rígidos separando Dumb Components (UI visual pura) de Smart Components / Custom Hooks (orquestração e API).
* **Isolamento de Banco Lógico vs Físico:** As fatias verticais do `aidd-master` são isoladas no código, mas compartilham as mesmas conexões e tabelas no mesmo schema relacional padrão.
* **Ausência de Gates de Carga/SLO:** Os gates validam sintaxe, segurança e testes unitários, mas não executam testes de carga sintéticos (K6/Locust) para garantir latência sob concorrência.

---

## 4. Resultado da Auditoria Global (`python ecossistema.py audit`)

Executada em 2026-09-16 contra o branch de trabalho:

```text
G_ECOSSISTEMA_INTEGRIDADE (ferramentas/skills/commands/AST)....................Passed
G_DRIFT_NUCLEO_COMPARTILHADO (nucleo master vs enterprise).....................Passed
G_HARNESS_COMPAT (artefatos multi-harness sincronizados).......................Passed
G_CLI_HELP_CONSISTENCIA (flags citadas vs add_argument)........................Passed
G_COMPONENTE_AGNOSTICO (componentes vs manifesto de harnesses).................Passed
G_ZERO_HEADLESS (modo interativo obrigatorio / zero headless)..................Passed
G_INFRA_COMPOSE (compose e init sql estaticos do aidd-ops).....................Passed
G_HADOLINT (melhores praticas OCI via Hadolint)................................Passed
G_TESTES_REAIS (pytest real por ferramenta em tools/)..........................FAILED (Exit Code 1)
G_DEPENDENCIAS_PIN_HASH (pin exato + hash criptografico).......................Passed
```

### Detalhamento de `G_TESTES_REAIS`:
* **Total Executado:** 2.211 aprovados, 2 falhas, 8 skipped (dentro do orçamento de 61).
* `aidd-forge`: 294 passed, 0 failed, 1 skipped [OK]
* `aidd-generator`: 1015 passed, 0 failed, 5 skipped [OK]
* `aidd-master`: 352 passed, **1 failed**, 1 skipped [FALHA]
* `aidd-enterprise`: 329 passed, **1 failed**, 1 skipped [FALHA]
* `aidd-ops`: 168 passed, 0 failed, 0 skipped [OK]
* `aidd-bridge`: 40 passed, 0 failed, 0 skipped [OK]
* `aidd-factory`: 13 passed, 0 failed, 0 skipped [OK]

#### Causa-Raiz Técnica da Falha Identificada:
* **Arquivo:** `tools/aidd-master/scripts/test_live.py` (e seu correspondente no enterprise).
* **Motivo:** O arquivo realiza requisições HTTP ativas (`urllib.request.urlopen("http://localhost:3000")`) em nível de módulo durante a fase de coleta do `pytest` (`Collection Error`), falhando com `ConnectionRefusedError: [WinError 10061]` quando nenhum servidor de produção local está previamente levantado.
* **Correção Recomendada:** Condicionar a execução do `test_live.py` a uma flag/marca explícita de teste e2e/live (`@pytest.mark.live` ou ignorar no `pytest.ini` padrão), evitando falha em pipelines de testes unitários offline.

---

## 5. Plano de Ação Recomendado

1. **Correção Imediata dos Testes:** Isolar e corrigir o teste quebrado em `aidd-master` e `aidd-enterprise` para restaurar o exit code 0 na auditoria.
2. **Atualização da CLI Raiz:** Integrar comandos de `aidd-factory` e `aidd-bridge` diretamente em `ecossistema.py`.
3. **Enforcement de Frontend:** Desenvolver gate de linting AST (ou regra ESLint personalizada) para impedir chamadas de dados diretas dentro de componentes puros de interface.
4. **AST Poliglota:** Introduzir parser baseado em Tree-sitter para auditar arquitetura em stacks fora do ecossistema Python.
