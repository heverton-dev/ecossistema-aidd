# Relatório de Análise e Melhoria: Pipeline Unificado de Orquestração com Acionamento Tríade

> **Data:** 21-09-2026  
> **Status:** AUDITADO / RASCUNHO EXECUTIVO  
> **Nota Atual:** 7.8/10  
> **Evidência:** Análise estática e dinâmica de `ecossistema.py` (1026 LOC), `tools/aidd-planner/` (`planner_engine.py`, 320 LOC), `componentes/compartilhado/skills/plan/`, `componentes/compartilhado/skills/orchestrate/`, 26 Quality Gates em `gates/`, 64 skills canônicas e 6 MCPs sincronizados.

---

## 1. Sumário Executivo

A governança do Ecossistema AIDD alcançou elevado grau de maturidade nas fases de **planejamento** (`aidd-planner` com JSON Schema e `aidd-plan` com planos fatiados) e nas barreiras de **qualidade pós-código** (26 Quality Gates mecânicos). 

No entanto, há uma lacuna estrutural na transição entre o planejamento e a execução:
1. O comando `/orchestrate` delega a execução entre Orca, Subagentes ou scripts soltos de forma manual e dependente de decisão do desenvolvedor no chat, gerando risco de concorrência ou ineficiência de tokens.
2. Não existe um motor determinístico capaz de receber uma lista de tarefas (ex: 20 passos sendo 15 assíncronos e 5 síncronos), particioná-los em **Git Worktrees efêmeros**, validar gates intermediários e convergir no branch principal.
3. Não há um **Acionamento Tríade Universal [CLI - Slash Command - Skill Runner]** padronizado para essa execução.

---

## 2. O que será CRIADO

| Componente | Tipo | Caminho Físico | Comprovação Auditável / Justificativa |
|---|---|---|---|
| **Contrato Unificado de Handoff** | Schema JSON | `componentes/compartilhado/specs/handoff-execucao.schema.json` | Define a estrutura determinística para tarefas paralelas (worktrees isolados) e sequenciais (join barrier), unificando `plan` e `planner`. Auditável via `jsonschema`. |
| **Quality Gate do Handoff** | Quality Gate (Lei #13) | `gates/G_PIPELINE_HANDOFF.py` + `tests/test_gate_pipeline_handoff.py` | Audita se qualquer plano de execução submetido cumpre o schema sem stubs e com testes atômicos declarados. Prova que reprova com exit 1 quando violado. |
| **Motor de Execução por Worktrees** | Script Core | `tools/aidd-master/scripts/orchestrator_pipeline.py` | Cria diretórios descartáveis via `git worktree add`, executa tickets em paralelo com isolamento de filesystem e RAM mínima (~0 MB), executa gates e faz merge automático. |
| **Compilador de Tickets do Plan** | Módulo CLI | `scripts/compilador_tickets_plano.py` | Lê `docs/planos/PLAN-<NNNN>-<slug>/` (`01-*.md` etc.), extrai os tickets atômicos estruturados pelo `/aidd-tickets` e gera `handoff_evolution.json`. |
| **Skill Runner Canônico** | Skill Multi-Harness | `componentes/compartilhado/skills/aidd-pipeline-runner/` | Skill canônica que implementa o runner executável e é sincronizada para todos os 7 harnesses (`.agents`, `.claude`, `.gemini`, etc.). |

---

## 3. O que será MUDADO

| Componente | Modificação | Comprovação Auditável / Justificativa |
|---|---|---|
| `ecossistema.py` | Adição dos comandos `pipeline`, `run-plan` e `tickets` no dispatcher central | Permite acionamento CLI imediato: `python ecossistema.py run-plan PLAN-0034` e `python ecossistema.py pipeline --handoff <json>`. Conecta a CLI central à Tríade. |
| `componentes/compartilhado/skills/plan/SKILL.md` | Encadeamento formal de handoff com `/aidd-spec` e `/aidd-tickets` | Elimina o plano em rascunho estático. Garante que todo item de plano contenha critérios binários e tickets tracer-bullet compiláveis. |
| `componentes/compartilhado/skills/orchestrate/SKILL.md` | Priorização do pipeline determinístico de worktrees como via padrão | Remove ambiguidades sobre criação manual de subagentes ou árvores de mesas filhas acidentais no Orca. |
| `tools/aidd-planner/src/core/planner_engine.py` | Inclusão da função `exportar_para_pipeline_execucao()` | Habilita o comando `python -m aidd_planner.cli export <caminho> --formato pipeline`, gerando diretamente o contrato de handoff para a meso-camada. |
| `AGENTS.md` e `docs/protocolos/` | Registro formal da Tríade de Acionamento do Pipeline | Documenta as vias `/run-plan`, `/pipeline`, CLI e Skill runner, mantendo conformidade com a Lei #6 (Agnosticismo) e Lei #7 (Developer in Control). |

---

## 4. O que será ELIMINADO

| Item a Eliminar | Racional e Impacto Auditável |
|---|---|
| **Bifurcação e Vibe Coding no Orchestrate:** | Fim da necessidade de o agente deliberar no chat sobre "como rodar" cada plano. A execução segue estritamente o grafo topológico de dependências definido no handoff JSON. |
| **Subagentes Concorrentes no Mesmo Workspace:** | Eliminação de qualquer tentativa de rodar múltiplos subagentes editando o mesmo diretório de trabalho sem isolamento de filesystem (prevenção de colisões e sobrescritas acidentais). |
| **Handoff em Prosa Informal:** | Fim de planos repassados para execução como texto livre. Somente planos validados pelo `G_PIPELINE_HANDOFF` com `exit 0` são despachados para execução. |

---

## 5. O que será MANTIDO (Garantia de Não-Regressão)

1. **Todos os 26 Quality Gates Canônicos:** Permanecem inalterados e funcionando como barreiras binárias inegociáveis (`python ecossistema.py audit`).
2. **Padrão-Ouro de Stack Tecnológica (Lei #11):** Next.js + TypeScript + Tailwind no Frontend, Python puro + SQLite WAL no Backend e OpenAPI 3.1.
3. **Quarteto Sine Qua Non (Lei #10):** `/docs` (Swagger), `/webhooks`, `/mcp` e `/docs/guia` obrigatórios em toda entrega.
4. **Tríade Canônica de Criação:** Fluxo 01 (`pure`), Fluxo 02 (`open`) e Fluxo 03 (`freedom`) continuam convergindo para `aidd-master` ➔ `aidd-enterprise` ➔ `aidd-ops`.
5. **Estrutura Histórica Documental:** Diretórios `docs/planos/` (`PLAN-<NNNN>-<slug>`), `docs/melhorias/` e `docs/issues/` permanecem intocados em sua integridade.
6. **Micro-ferramentas Procedimentais:** `aidd-grill`, `aidd-spec`, `aidd-tickets`, `aidd-tdd`, `aidd-diagnose` e `aidd-handoff` continuam operando e passam a ser os fornecedores primários de dados do novo pipeline.

---

## 6. Próximo Passo Determinístico

Proceder à execução dos tickets atômicos estruturados na pasta dedicada `docs/issues/pipeline-orquestracao-triade/`, seguindo rigorosamente a ordem sequencial declarada em seu `SESSOES.md`.
