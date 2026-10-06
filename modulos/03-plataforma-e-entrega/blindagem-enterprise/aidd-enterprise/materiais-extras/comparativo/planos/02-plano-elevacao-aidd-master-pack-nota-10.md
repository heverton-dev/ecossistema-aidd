# Plano de Ação: Elevação do aidd-master-pack para Nota 10.0 em Todas as Camadas

> **Projeto:** `aidd-master-pack` (Versão Atual: v5.1.0 Enterprise Anti-Fail / Commit base: `674368c`)  
> **Nota Atual Consolidada:** 9.44 / 10.0  
> **Meta:** Atingir 10.0+ em todas as 5 dimensões técnicas, tornando-o o padrão definitivo da indústria.  
> **Fundamentação Técnica Integrada:** Consolidação da Suíte Elite Engineering (`SESSAO_ELITE_ENGINEERING_2026-09-01.md`) + Orquestração ORCA ADE + Subagentes Efêmeros com Descarte de Contexto + Modularização Granular por Fatia + Interface Zero Fricção (/compose) + Protocolo Caveman Ultra.

---

## 1. Diagnóstico e Alinhamento com a Suíte Elite Engineering (2026-09-01)

A sessão de Elite Engineering consolidou os pilares mais avançados de confiabilidade industrial no `aidd-master-pack`:

### A. Itens Já Implementados e Mergeados em `main` (`commit 674368c`):
1. **Circuit Breakers Nativos:** `src/core/circuit_breaker.py` — Prevenção de falhas em cascata em chamadas externas.
2. **Testes de Mutação AST:** Integração do `mutmut` no pipeline mecânico de testes unitários.
3. **Chaos Engineering:** `scripts/gates/G_CHAOS.py` — Simulação estocástica de quedas de rede e processos.
4. **Logs Estruturados:** `src/core/logs.py` com `structlog` injetando contexto JSON serializado.
5. **Row-Level Security (RLS) no SQLite Multi-Tenant:** `RLSConnection` corrigida com injeção automática de `tenant_id` e suporte completo a `cursor()`.
6. **Fuzzing Contínuo de API:** `src/core/fuzzing.py` integrado ao gate `G_QUALIDADE`.

---

## 2. Incorporação das Worktrees Pendentes de Elite Engineering

Para que o Plano 2 atinja a Nota 10.0+ absoluta, o roadmap incorpora formalmente as entregas das worktrees `elite-11-otel` e `elite-12-arch`:

### Worktree `elite-11-otel` — Observabilidade Distribuída & Segurança CVE
* **TracerProvider & Tracing Distribuído:** `src/core/opentelemetry.py` com fallback para exportador console, decorator `@trace_span(name)`, middleware FastAPI propagando trace context e injeção do `trace_id` em cada log do `structlog`.
* **Métricas de SLA/SLO:** `src/core/metrics.py` com histograma `http_request_duration_seconds` [0.05, 0.1, 0.2, 0.5, 1.0, 2.0] e gerador de dashboard HTML Prometheus com alerta visual (badge vermelho para p99 > 200ms).
* **Auditoria de Vulnerabilidades CVE no Gate:** Atualização de `scripts/gates/G_SEGURANCA.py` com varredura ativa `pip-audit --format=json -r requirements.txt`, reprovando com `exit 1` em vulnerabilidades HIGH/CRITICAL.

### Worktree `elite-12-arch` — Linter AST de Arquitetura & Auto-Healing
* **Linter de Bounded Context AST:** `scripts/gates/G_ARQUITETURA.py` varre recursivamente `src/modules/` bloqueando imports diretos entre fatias verticais (`modules.crm` ➔ `modules.erp`), permitindo apenas `core.*` ou `EventBus`. Reprova com `exit 1` em violações.
* **Orquestrador com Auto-Healing:** `scripts/run_all.py` executa todos os gates em sequência. Se um gate falhar, aciona `scripts/autofix.py` (formatação `black`, limpeza de `*.pyc`/`__pycache__`) e re-executa antes de reprovar definitivamente.
* **Design System Corporativo CSS:** `templates/static/design-system.css` padronizado com variáveis CSS `:root`, classes `.studio-card`, `.metric-badge`, scrollbars sutis de 4px e injeção automática no `<head>` do Swagger/OpenAPI.

---

## 3. Orquestração de Subagentes com Descarte Imediato de Contexto (Context-Purge Engine)

O `aidd-master-pack` formaliza a sinfonia entre o **Maestro Mecânico Python** e os **Subagentes Cognitivos Descartáveis**:

```
                  SCRIPTS/AIDD.PY (Maestro Mecânico)
                             │
            ┌────────────────┴────────────────┐
            ▼                                 ▼
   MECÂNICA DETERMINÍSTICA           SUBAGENTES COGNITIVOS EFÊMEROS
  (Zero Token / Python Puro)        (Cognição Sob Demanda / Descarte)
  ─────────────────────────         ─────────────────────────────────
  • Cria fatias e diretórios.       • Modela regras de domínio ricas.
  • Injeta Shared Kernel e Result.  • Escreve rotas e regras de negócio.
  • Executa Circuit Breaker e RLS.  • Audita Clean Architecture.
  • Valida AST e concorrência WAL.  • SESSÃO DESTRUÍDA APÓS CONCLUSÃO.
```

- Cada subagente recebe apenas a especificação da sua fatia (`SPEC-ARQUITETURA.md` filtrada) com um prompt de ~1.200 tokens.
- O subagente grava os arquivos da fatia e **sua sessão é destruída imediatamente**. O histórico não contamina as próximas etapas.

---

## 4. Auto-Descoberta de Frota & Fallback em Cascata no ORCA ADE

Para garantir que o comando `aidd.py compose --orca` funcione em qualquer máquina sem erro de dependência de ferramentas:

```
                              INÍCIO DO RUNNER ORCA
                                        │
                                        ▼
                      ┌────────────────────────────────────┐
                      │ 1. Auto-Descoberta de Ferramentas  │
                      │    (which claude, codex, agy, etc) │
                      └─────────────────┬──────────────────┘
                                        │
             ┌──────────────────────────┴──────────────────────────┐
             ▼                                                     ▼
   DETECTOU MÚLTIPLOS AGENTES                             DETECTOU APENAS 1 AGENTE
(Ex: Tem Claude e Codex no host)                        (Ex: Usuário só tem Antigravity)
             │                                                     │
             ▼                                                     ▼
ROTEIA POR ESPECIALIDADE                               MODO "AGENTE ÚNICO ISOLADO"
• Arquiteto  ➔ Claude                                  • Todos os workers usam Antigravity!
• Database   ➔ Codex                                   • MAS rodam em Worktrees separadas
                                                       • Mantém o ganho de contexto limpo!
```

- **Customização no `.env`:** O usuário pode fixar `ORCA_DEFAULT_HARNESS=claude` (ou `antigravity`, `codex`, `ollama`), adaptando toda a esteira sem quebras.

---

## 5. Modularização Granular por Fatia e Camada

Cada fatia vertical opera em micro-ambientes com regras dedicadas:
* `camada-database/`: regras estritas de SQLite WAL, Postgres, chaves estrangeiras, RLSConnection e Database MCP.
* `camada-servicos/`: regras de Result Monad, Circuit Breaker, EventBus e proibição de acoplamento entre módulos.
* `camada-routes-api/`: OpenAPI 3.1, Swagger com `design-system.css`, Fuzzing contínuo e servidor MCP JSON-RPC 2.0.
* `camada-frontend/`: Impeccable UI Tailwind, acessibilidade WCAG 2.1 e Chrome DevTools MCP.

---

## 6. Interface Humana Zero Fricção (Zero Terminal Barrier)

* **Slash Command Nativo:** `/compose <módulos>` ou `/aidd-pack <módulos>` no chat (ex: `/compose crm erp billing`).
* **Linguagem Natural:** Intent router no `AGENTS.md` converte pedidos como *"arquitetura corporativa para..."* em execução direta.
* **1-Clique Desktop:** `iniciar.bat` (Windows) / `iniciar.sh` (Linux/Mac) executando o setup e abrindo os portais locais.

---

## 7. Protocolo Tríplice de Economia Severa de Tokens (Caveman Ultra)

1. **ENTRADA (Instruções em Inglês):** Redução de 30% a 50% de consumo BPE na leitura de regras.
2. **PROCESSAMENTO (Internal Thinking em English Caveman):** CoT ultra-denso (3 a 5 linhas): *"inspect ast, verify gate, compile module, test 0"*.
3. **SAÍDA / OUTPUT (Português do Brasil - PT-BR de Alto Padrão):** Entrega de código completo, com Result Monad, tipado, livre de stubs e documentado em PT-BR.

---

## 8. Cronograma de Execução Atualizado

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                  CRONOGRAMA DE ELEVAÇÃO: aidd-master-pack ➔ NOTA 10.0+           │
├──────────────────────────────────────────────────────────────────────────────────┤
│ SPRINT 1: Fechamento das Worktrees Elite (elite-11-otel Tracing + elite-12-arch) │
│ SPRINT 2: Gate G_ARQUITETURA AST de Bounded Context + Auto-Healing scripts/run_all│
│ SPRINT 3: Gate G_SEGURANCA com pip-audit de CVEs HIGH/CRITICAL                   │
│ SPRINT 4: Engine de Subagentes Efêmeros com Descarte Imediato de Contexto        │
│ SPRINT 5: Auto-Descoberta de Frota & Fallback Universal no ORCA ADE              │
│ SPRINT 6: Granularização por Fatias e Camadas (Micro-Ambientes com AGENTS/MCPs)  │
│ SPRINT 7: Camada Zero Fricção (Slash Command /compose + Intent Router no Chat)   │
│ SPRINT 8: Protocolo Tríplice Caveman Ultra no AGENTS.md e IDEs                   │
│ SPRINT 9: DatabaseAdapter Poliglota (PostgreSQL / Supabase / SQLite WAL)         │
│ SPRINT 10: Exportador Next.js + Gate G_PERFORMANCE com Métricas OpenTelemetry    │
└──────────────────────────────────────────────────────────────────────────────────┘
```
