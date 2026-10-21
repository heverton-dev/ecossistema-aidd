# Painel Canônico de Auditorias Osmani da Tríade AIDD

Este diretório registra as auditorias profundas de ponta a ponta (Pipeline Osmani) executadas na esteira de geração dos 3 motores do Ecossistema AIDD.

---

## Status da Tríade de Motores

| Fluxo | Motor | Geração Inicial | Auditoria Osmani | Status Atual | Diretório de Evidências |
|---|---|---|---|---|---|
| **Fluxo 03** | `aidd-freedom` | Concluída | **100% Concluída** | **HOMOLOGADO** | [fluxo-03-freedom/](fluxo-03-freedom/) |
| **Fluxo 02** | `aidd-open` | Concluída | **Pendente** | **Aguardando Início** | `fluxo-02-open/` (Próximo) |
| **Fluxo 01** | `aidd-pure` | Em Execução | **Pendente** | **Em Andamento (TDD)** | `fluxo-01-pure/` |

---

## 1. Fluxo 03 — Freedom (`aidd-freedom`) [CONCLUÍDO]

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

## 2. Fluxo 02 — Open (`aidd-open`) [NA FILA]

- **Status da Geração:** Concluída com sucesso pelo agente paralelo.
- **Próximo Passo:** Inicializar scaffold `fluxo-02-open/`, mapear micropipelines de motores open-source (Strapi, Directus, n8n, etc.) e executar a bateria completa de auditoria Osmani.

---

## 3. Fluxo 01 — Pure (`aidd-pure`) [EM EXECUÇÃO]

- **Status da Geração:** Agente paralelo em execução contínua (esteira TDD pura de 8 fases).
- **Ação:** Monitoramento passivo até finalização da geração antes do disparo da auditoria Osmani correspondente.
