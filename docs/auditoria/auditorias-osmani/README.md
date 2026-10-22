# Painel Canônico de Auditorias Osmani da Tríade AIDD

Este diretório registra as auditorias profundas de ponta a ponta (Pipeline Osmani) executadas na esteira de geração dos 3 motores do Ecossistema AIDD.

---

## Status da Tríade de Motores

| Fluxo | Motor | Geração Inicial | Auditoria Osmani | Status Atual | Diretório de Evidências |
|---|---|---|---|---|---|
| **Fluxo 03** | `aidd-freedom` | Concluída | **100% Concluída** | **HOMOLOGADO** | [fluxo-03-freedom/](fluxo-03-freedom/) |
| **Fluxo 02** | `aidd-open` | Concluída | **100% Concluída** | **HOMOLOGADO** | [fluxo-02-open/](fluxo-02-open/) |
| **Fluxo 01** | `aidd-pure` | Concluída | **100% Concluída** | **HOMOLOGADO** | [fluxo-01-pure/](fluxo-01-pure/) |

---

## 1. Fluxo 03 — Freedom (`aidd-freedom`) [100% HOMOLOGADO]

- **Escopo Auditado:** 10 micropipelines (Forge, Planner, Bridge, Master, Dispatch, Engine, Barrier, Enterprise, Ops, Macro-Gates).
- **Entregas Principais:**
  - Soberania do Modo Claro (Light Mode Sovereign) na Lei #11 de [AGENTS.md](../../AGENTS.md).
  - Templates TanStack atualizados com primitivos bi-modais (`DataTable`, `KanbanBoard`, `MetricCard`, `tokens.css`).
  - Removido lock-in hardcoded de cores escuras na casca do frontend.
  - Correção determinística de detecção de raiz em `G_ENV_ROT.py`.
  - Sincronização SHA-256 de `G_TESTES.py` em `componentes/compartilhado/CATALOGO.json`.
  - 7/7 Quality Gates aprovados no app piloto com `exit code 0`.
- **Relatório Detalhado:** [fluxo-03-freedom/README.md](fluxo-03-freedom/README.md) e [TICKETS-CORRECAO.md](fluxo-03-freedom/TICKETS-CORRECAO.md).

---

## 2. Fluxo 02 — Open (`aidd-open`) [100% HOMOLOGADO]

- **Escopo Auditado:** Pipeline multi-serviço (Fase 1 a 9, Gateway FastAPI, Frontend TanStack, Compose, Gates).
- **Entregas Principais:**
  - `TCK-OPEN-01` (Paridade Frontend/Backend): 14/14 rotas conectadas na UI via `ModulosPage.tsx`, atingindo 100% de paridade no `G_UI_API_PARITY`.
  - `TCK-OPEN-02` (Craft Visual & Modo Claro): `tokens.css` OKLCH injetado e referências Next.js eliminadas de `frontend_generator.py`.
  - `TCK-OPEN-03` (Trava de Terminação): Encerramento mecânico e sinalização anti-loop implementados.
  - Testes do backend (8/8) e build do frontend (`npm run build`) 100% verdes.
- **Relatório Detalhado:** [fluxo-02-open/README.md](fluxo-02-open/README.md) e [fluxo-02-open/TICKETS-CORRECAO.md](fluxo-02-open/TICKETS-CORRECAO.md).

---

## 3. Fluxo 01 — Pure (`aidd-pure`) [100% HOMOLOGADO]

- **Escopo Auditado:** Pipeline do zero puro (8 fases TDD Red-Green, Monólito Modular VSA, FastAPI + SQLite WAL + React Vite).
- **Entregas Principais:**
  - `TCK-PURE-01` (Paridade Frontend/Backend): Página `TasksPage.tsx` criada integrando as 3 visões (`ChecklistView`, `KanbanView`, `ListView`), seletores de lista, formulário de adição, botões de exclusão, alternância de conclusão, movimentação de status e revogação de tokens de sessão. `G_UI_API_PARITY` subiu de 5.88% para **100.00%**.
  - `TCK-PURE-02` (Trava Determinística Anti-Loop Reflexivo): Injetada a trava de encerramento em todos os orquestradores da tríade (`pipeline_completo.py`, `pipeline_factory.py`, `pipeline_bridge.py`, `orchestrator_pipeline.py`, `orquestrador_sincrono.py`), criação da flag `.aidd/PIPELINE_CONCLUIDO.flag`, bloqueio no hook `anti_headless_subagent_hook.py` e regras em `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`.
  - Backend com 207/207 testes passando em 18s e build do frontend aprovado via Vite em 16.68s.
- **Relatório Detalhado:** [fluxo-01-pure/README.md](fluxo-01-pure/README.md) e [fluxo-01-pure/TICKETS-CORRECAO.md](fluxo-01-pure/TICKETS-CORRECAO.md).
