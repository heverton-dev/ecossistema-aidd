# Backlog Consolidado de Micro-Tickets — AIDD-Osmani (Fluxo 01 Pure)

> **Origem:** Auditoria Factual dos Micropipelines da Máquina Geradora `aidd-pure` e Aplicação Piloto `TaskFlow-Pure`.  
> **Diretiva:** Lei #10 (Quarteto Sine Qua Non Dinâmico), Lei #11 (Padrão-Ouro Stack), Lei #13 (Todo Portão Deve Provar que Morde).  
> **Total de Tickets:** 2 Micro-Tickets Mapeados (2 RESOLVIDOS)  

---

## Matriz de Priorização de Tickets

| Ticket ID | Etapa / Ferramenta | Descrição Resumida | Severidade | Status | Portão Vinculado |
| :--- | :--- | :--- | :---: | :---: | :---: |
| **`TCK-PURE-01`** | Frontend (`app/frontend/src`) | Conectar as rotas reais de tarefas, listas e autenticação na UI para elevar paridade | **CRÍTICA** | **RESOLVIDO** | `G_UI_API_PARITY` (Lei #10) |
| **`TCK-PURE-02`** | `08_implementador.py` / Orquestradores | Trava determinística anti-loop reflexivo e critério de parada binário em todos os fluxos | Alta | **RESOLVIDO** | `G_ZERO_HEADLESS` (Lei #7) |

---

## Detalhamento das Resoluções Factuais

### [TCK-PURE-01] Paridade Frontend vs Backend
- **Problema Anterior:** Backend com 11 rotas reais de aplicação (autenticação, task-lists, tasks, tokens), mas a UI só chamava 1 rota (TPE = 5.88%), reprovando `G_UI_API_PARITY`.
- **Ação Executada:**
  1. Criação de `TasksPage.tsx` integrando as 3 visões (`ChecklistView`, `KanbanView`, `ListView`), seletores de lista, formulário de adição, botões de exclusão, alternância de conclusão, movimentação de status e revogação de tokens de sessão.
  2. Ajuste das rotas completas `/api/...` em `lib/api.ts` e exportação do objeto `api` compatível.
  3. Adição da rota `/tasks` em `App.tsx` e no menu lateral de `Layout.tsx`.
- **Resultado Factual:** `G_UI_API_PARITY` saltou de 5.88% para **100.00%** (11/11 rotas conectadas na interface), e `npm run build` gerou o bundle de produção em 16.68s com exit code 0.

### [TCK-PURE-02] Trava Anti-Loop Reflexivo em Todos os Fluxos
- **Problema Anterior:** O agente paralelo ficou rodando por 3 horas sem avançar porque não havia uma trava mecânica de parada pós-`PIPELINE_FINISHED rc=0`.
- **Ação Executada:**
  1. Injetada a gravação atômica de `.aidd/PIPELINE_CONCLUIDO.flag` e o aviso terminal `🛑 [TERMINATION_SIGNAL]` em:
     - `scripts/orquestrador_sincrono.py` (Orquestrador Unificado da Tríade)
     - `pipeline_completo.py` (Fluxo 01 Pure Motor)
     - `pipeline_factory.py` (Fluxo 02 Open Motor)
     - `pipeline_bridge.py` (Fluxo 03 Freedom Motor)
     - `orchestrator_pipeline.py` (Orquestrador de Worktrees)
  2. Atualizado o hook `anti_headless_subagent_hook.py` (compartilhado e Claude) para interceptar e bloquear qualquer subagente caso `.aidd/PIPELINE_CONCLUIDO.flag` esteja presente.
  3. Atualizadas as diretivas agênticas em `AGENTS.md`, `CLAUDE.md` e `GEMINI.md` com a regra mandatória de parada imediata sob `[TERMINATION_SIGNAL]`.
- **Resultado Factual:** Zero possibilidade de loops infinitos; o encerramento do pipeline desarma imediatamente novos comandos e força a emissão do relatório final.
