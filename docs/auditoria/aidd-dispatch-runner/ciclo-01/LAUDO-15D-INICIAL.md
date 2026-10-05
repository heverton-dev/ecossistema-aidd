# Template de Auditoria de Ferramenta (Lens 15-D)

Este documento descreve a estrutura canônica para auditar qualquer ferramenta (Skill/Tool) do ecossistema, dissecando sua arquitetura através do framework Lens 15-D (The Agentic Anatomical Matrix).

## 1. Identificação da Ferramenta
- **Nome da Ferramenta:** `aidd-dispatch-runner` (`aidd-dispatch`)
- **Descrição Breve:** Despachador determinístico de fatias verticais VSA em lotes topológicos (DAG via algoritmo de Kahn) em Git Worktrees efêmeras com validação de fronteiras de arquivo e convergência no monolito modular.
- **Comando de Gatilho:** `/dispatch`, `/aidd-dispatch`, `python ecossistema.py dispatch`

## 2. A Matriz Anatômica (Lens 15-D)

### Fase 1: Governança e Blindagem
- **D1. Contratos e Regras:** Regras formalizadas em `schemas/vsa_dispatch_schema.json` e `SKILL.md`: ordenação DAG sem ciclos, barreira de gates por fatia (`exit 0`/`exit 1`), isolamento estrito em worktrees, fronteira de arquivos esperados (`arquivos_esperados`) e conformidade com o Quarteto Sine Qua Non.
- **D2. Input e Gatilhos:** Interface via CLI do ecossistema `python ecossistema.py dispatch --planner <PLANNER.json>` ou `--dispatch <vsa_dispatch.json>`, com suporte a `--dry-run` e `--workers`.
- **D3. Raio de Impacto e Isolamento:** Cada fatia executa em worktree isolada `.worktrees/<slice_id>` sob branch `slice/<slice_id>`, com validação de que alterações não vazem para fora dos arquivos permitidos da fatia.
- **D4. Componentes e Fractalidade:** Implementação em `tools/aidd-master/scripts/dispatch_pipeline.py` integrada na CLI unificada raiz `ecossistema.py`.

### Fase 2: O Chão de Fábrica (Workflow Agêntico)
- **D5. Visão e Escopo:** Despachar e convergir fatias verticais VSA de maneira concorrente e ordenada topologicamente garantindo que dependências converjam antes de seus consumidores.
  - **[Estágio 1 - Compilação Topológica DAG] D6. O que o Estágio Faz:** Compila o PLANNER.json em lotes ordenados usando algoritmo de Kahn.
  - **[Estágio 1 - Compilação Topológica DAG] D7. O que o Estágio Recebe:** Arquivo `PLANNER.json`.
  - **[Estágio 1 - Compilação Topológica DAG] D8. O que o Estágio Processa:** Resolução de dependências e detecção de ciclos.
  - **[Estágio 1 - Compilação Topológica DAG] D9. O que o Estágio Entrega:** Manifesto `vsa_dispatch.json` estruturado.
  - **[Estágio 2 - Execução Concorrente em Lotes] D6. O que o Estágio Faz:** Cria worktrees e despacha as fatias independentes do lote ativo.
  - **[Estágio 2 - Execução Concorrente em Lotes] D7. O que o Estágio Recebe:** Lote de fatias verticais.
  - **[Estágio 2 - Execução Concorrente em Lotes] D8. O que o Estágio Processa:** Execução de suítes de teste de cada fatia.
  - **[Estágio 2 - Execução Concorrente em Lotes] D9. O que o Estágio Entrega:** Fatias testadas e commitadas localmente.
  - **[Estágio 3 - Convergência e Suíte Master] D6. O que o Estágio Faz:** Realiza merge sequencial das fatias aprovadas e roda suíte pós-merge.
  - **[Estágio 3 - Convergência e Suíte Master] D7. O que o Estágio Recebe:** Fatias aprovadas no lote.
  - **[Estágio 3 - Convergência e Suíte Master] D8. O que o Estágio Processa:** Merge na árvore base e remoção física das worktrees.
  - **[Estágio 3 - Convergência e Suíte Master] D9. O que o Estágio Entrega:** Monolito modular convergido e íntegro.
- **D10. Orquestração e Topologia:** Topologia DAG hierárquica por lotes determinísticos com portões de validação por fatia.

### Fase 3: Resiliência e Economia (Engenharia Operacional)
- **D11. Tratamento de Exceções e Fallback:** Interrupção imediata na falha de qualquer fatia antes do merge, impedindo que branches quebrados poluam o master.
- **D12. Observabilidade e Frugalidade:** Execução determinística em Python/Git sem consumo de LLM na coordenação de processos locais.

### Fase 4: O Inspetor e a Expedição (Validação)
- **D13. Quality Gates (Portões):** Portão binário soberano `gates/G_DISPATCH_PIPELINE_VSA.py` validando o manifesto e ausência de ciclos/stubs com exit 0.
- **D14. Critério de Rejeição (Rollback):** Falha na validação de uma fatia interrompe o lote e preserva o estado estável da base.
- **D15. Output Consolidado e Handoff:** Manifesto `vsa_dispatch.json` auditado e fatias VSA convergidas com sucesso.

---

## 3. Matriz de Avaliação da Execução
- [x] A ferramenta isolou seu raio de impacto corretamente? Sim, isolamento total em `.worktrees/<slice_id>`.
- [x] O workflow seguiu as fases sem alucinações de LLM em tarefas mecânicas? Sim, motor 100% determinístico em Python e Git.
- [x] O output final passou em todos os Quality Gates e emitiu o Handoff? Sim, validado por `G_DISPATCH_PIPELINE_VSA.py` com exit 0.
