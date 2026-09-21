# Relatório de Análise e Melhoria: Meso-Camada da Tríade Canônica (Aplicações Completas)

> **Data:** 21-09-2026  
> **Iniciativa:** Meso-Camada da Tríade Canônica (`aidd-dispatch-pipeline`)  
> **Status:** AUDITADO / APROVADO PARA EXECUÇÃO  
> **Nota Atual:** 8.1/10 (Gap na distribuição de fatias VSA em worktrees paralelos e convergência macro)  
> **Evidência:** Análise estrutural e de conformidade de `ecossistema.py`, `scripts/orquestrador_sincrono.py` (578 LOC), `tools/aidd-planner/` (`planner_engine.py`, `planner_schema.json`), `tools/aidd-master/`, `tools/aidd-generator/`, `tools/aidd-factory/`, `tools/aidd-bridge/`, 26 Quality Gates e especificações de contratos de handoff em `componentes/compartilhado/specs/`.

---

## 1. Sumário Executivo e Arquitetura Alvo

A criação de aplicações completas no Ecossistema AIDD apoia-se no fluxo:
```
[FORGE] ➔ [PRÉ-PLANO (Grill + Spec)] ➔ [PLANNER] ➔ [DISPATCH-PIPELINE] ➔ [ENGINE (Pure/Open/Freedom)] ➔ [MASTER CONVERGENCE]
```

Atualmente, o ecossistema possui:
1. **Governança e Hardening:** `aidd-forge` robusto, regras canônicas inegociáveis e 26 Quality Gates com provas automatizadas de reprovação (Lei #13).
2. **Especificação e Intake:** `aidd-grill` e `aidd-spec` para resolução de invariantes e geração de BDD/OpenAPI sem stubs.
3. **Planejamento Polimórfico:** `aidd-planner` gerando e validando `PLANNER.json` com DDD Bounded Contexts, BDD Gherkin, infraestrutura e Quarteto Sine Qua Non (`/docs`, `/webhooks`, `/mcp`, `/docs/guia`).
4. **Engines Especialistas:** `aidd-generator` (Fluxo 01 Pure), `aidd-factory` (Fluxo 02 Open) e `aidd-bridge` (Fluxo 03 Freedom).
5. **Harmonização e Produção:** `aidd-master` (Monólito Modular VSA), `aidd-enterprise` (auditoria SHA-256) e `aidd-ops` (sizing e VPS Docker).

### O Gap Crítico da Meso-Camada:
No estado atual, o despacho entre o `PLANNER.json` e as Engines especialistas em `scripts/orquestrador_sincrono.py` ocorre de forma monolítica e linear com payloads estáticos/mockados. Não existe o **motor determinístico de despacho fatiado (`aidd-dispatch-pipeline`)** capaz de:
- Traduzir os Bounded Contexts e fatias VSA do `PLANNER.json` em um **Grafo Acíclico Dirigido (DAG topológico)**;
- Distribuir a execução das fatias independentes em **Git Worktrees paralelos e efêmeros** com zero interferência de filesystem;
- Aplicar a **Barreira de Validação** (Quality Gates por fatia com teste real e prova de que morde) antes da mesclagem;
- Realizar o merge atômico e a **Convergência Macro** no núcleo canônico do `aidd-master` (Monólito Modular VSA + Next.js).

---

## 2. O que será CRIADO

| Componente | Tipo | Caminho Físico | Explicação e Comprovação Auditável |
|---|---|---|---|
| **Contrato de Grafo Topológico VSA** | Schema JSON | `componentes/compartilhado/specs/vsa-topological-dispatch.schema.json` | Define a estrutura determinística para fatias verticais VSA, dependências topológicas (DAG), parâmetros de isolamento (worktree efêmero) e gates de barreira por fatia. Auditável via `jsonschema.Draft7Validator`. |
| **Quality Gate G_DISPATCH_PIPELINE_VSA** | Quality Gate (Lei #13) | `gates/G_DISPATCH_PIPELINE_VSA.py` + `tests/test_gate_dispatch_pipeline_vsa.py` | Audita se o manifesto de fatias VSA atende a todos os critérios: ausência de dependências circulares no DAG, isolamento estrito por branch/worktree, testes reais declarados e barreira de sincronização sem stubs. Falha com `exit 1` comprovado sob violação. |
| **Motor Central do aidd-dispatch-pipeline** | Módulo Core | `tools/aidd-master/scripts/dispatch_pipeline.py` | Recebe o `PLANNER.json`, compila a ordem topológica das fatias VSA, provisiona os Git Worktrees (`git worktree add -b slice/<nome>`), dispara a engine especialista em cada worktree, valida os gates locais e executa o fast-forward merge na barreira de convergência. |
| **Roteador Polimórfico de Engines** | Módulo Core | `tools/aidd-master/scripts/engine_router.py` | Adapta os requisitos de cada fatia para os inputs exatos da engine correspondente: `aidd-generator` (ciclo TDD Red-Green), `aidd-factory` (curadoria open-source + fatias de integração) e `aidd-bridge` (desacoplamento low-code e schema mapping). |
| **Barreira de Validação e Fusão Macro** | Módulo Core | `tools/aidd-master/scripts/vsa_join_barrier.py` | Executa a barreira de sincronização: roda `ecossistema.py audit` e testes de fatia antes de integrar ao branch `master`/`main`, garantindo que nenhuma regressão atinja o Monólito Modular VSA. |
| **Skill Runner Canônico da Meso-Camada** | Skill Multi-Harness | `componentes/compartilhado/skills/aidd-dispatch-runner/` | Skill canônica que encapsula a meso-camada e é sincronizada para todos os 7 harnesses (`.agents`, `.claude`, `.gemini`, `.cursor`, `.windsurf`, `.cline`, `.trae`). |

---

## 3. O que será MUDADO

| Componente | Modificação | Explicação e Comprovação Auditável |
|---|---|---|
| `scripts/orquestrador_sincrono.py` | Refatoração das etapas 03 e 04 | Substitui a chamada monolítica e mocks fixos ("RegistroPrincipal") pela chamada do `dispatch_pipeline.py`, consumindo o `PLANNER.json` polimórfico real e orquestrando as fatias em worktrees isolados. |
| `tools/aidd-planner/aidd_planner/core/planner_engine.py` | Inclusão de `compilar_grafo_topologico_vsa()` | Expõe método canônico para compilar os Bounded Contexts DDD e fatias em uma lista ordenada com dependências explícitas e comandos de teste associados. |
| `tools/aidd-planner/aidd_planner/cli.py` | Adição do comando `export-dispatch` | Permite gerar deterministicamente o `VSA_DISPATCH.json` a partir de qualquer `PLANNER.json` via CLI: `python -m aidd_planner.cli export-dispatch PLANNER.json`. |
| `ecossistema.py` | Adição do comando `dispatch` e suporte no `run-fluxo` | Permite disparar o pipeline diretamente via terminal: `python ecossistema.py dispatch --planner <caminho>` ou como sub-etapa síncrona nos comandos `pure`, `open` e `freedom`. |
| `componentes/compartilhado/skills/aidd-planner-runner/SKILL.md` | Atualização do fluxo de handoff | Vincula o encadeamento formal: `/aidd-grill` (intake DDD) ➔ `/aidd-spec` (contratos BDD/OpenAPI) ➔ `aidd-planner` ➔ `aidd-dispatch-pipeline`. |
| `AGENTS.md` e `GEMINI.md` | Registro canônico do Foco 02 da Tríade | Documenta a meso-camada, seus comandos e regras invioláveis de execução por fatias sem stubs. |

---

## 4. O que será ELIMINADO

| Item a Eliminar | Racional e Impacto Auditável |
|---|---|
| **Geração Monolítica Não-Fatiada:** | Eliminação da prática de submeter uma aplicação inteira diretamente a uma única passada de engine sem granularidade de fatias verticais VSA. Cada Bounded Context passa a ter seu próprio ciclo atômico. |
| **Payloads Mockados / Fixos em Scripts:** | Remoção dos dicionários estáticos mockados em `scripts/orquestrador_sincrono.py` (linhas 178-221 e 274-300). Toda a informação passa a fluir do `PLANNER.json` e dos contratos formais de handoff. |
| **Concorrência Suja em Sistema de Arquivos:** | Fim de qualquer execução paralela no diretório raiz sem isolamento. Todo processamento concorrente de fatias ocorrerá em diretórios temporários via `git worktree`. |
| **Bifurcação Informal no Orchestrate:** | Eliminação de decisões discricionárias do agente no chat sobre como particionar módulos de aplicação. O DAG topológico determina a sequência sem vibe coding. |

---

## 5. O que será MANTIDO (Garantia de Não-Regressão)

1. **26 Quality Gates Canônicos:** Permanecem 100% íntegros e mandatórios (`python ecossistema.py audit`).
2. **Padrão-Ouro de Stack Tecnológica (Lei #11):** Next.js + TypeScript + Tailwind CSS no Frontend; Python FastAPI puro + SQLite WAL (ou PostgreSQL) no Backend; OpenAPI 3.1.
3. **Quarteto Sine Qua Non Dinâmico (Lei #10):** Obrigatório em 100% dos módulos (`/docs`, `/webhooks`, `/mcp`, `/docs/guia`).
4. **Tríade Canônica de Criação:** Fluxo 01 (`pure`), Fluxo 02 (`open`), Fluxo 03 (`freedom`), mantendo compatibilidade total com os aliases e CLI existentes.
5. **Arquitetura aidd-master:** Convergência inegociável em Monólito Modular VSA (fatias verticais de domínio + camada horizontal compartilhada).
6. **Integridade das Camadas Macro:** `aidd-enterprise` (auditoria e blindagem SHA-256) e `aidd-ops` (sizing, VPS Docker e Uptime Kuma) permanecem como o funil final da entrega.

---

## 6. Próximo Passo Determinístico

Proceder com a execução sequencial do plano de issues estruturado em `docs/issues/meso-camada-triade-canonica/`, iniciando pela `ISSUE-MESO-0001` até a `ISSUE-MESO-0008` conforme mapeado em seu `SESSOES.md`.
