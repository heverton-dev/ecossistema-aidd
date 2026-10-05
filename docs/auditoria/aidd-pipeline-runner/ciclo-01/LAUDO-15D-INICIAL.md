# Template de Auditoria de Ferramenta (Lens 15-D)

Este documento descreve a estrutura canônica para auditar qualquer ferramenta (Skill/Tool) do ecossistema, dissecando sua arquitetura através do framework Lens 15-D (The Agentic Anatomical Matrix).

## 1. Identificação da Ferramenta
- **Nome da Ferramenta:** `aidd-pipeline-runner` (`aidd-pipeline`, `run-plan`)
- **Descrição Breve:** Orquestrador determinístico de execução paralela em Git Worktrees efêmeras com barreira de sincronização (join barrier), compilação de planos e validação rigorosa de handoff JSON.
- **Comando de Gatilho:** `/pipeline`, `/run-plan`, `python ecossistema.py run-plan`, `python ecossistema.py pipeline`

## 2. A Matriz Anatômica (Lens 15-D)

### Fase 1: Governança e Blindagem
- **D1. Contratos e Regras:** Contrato formalizado em `schemas/handoff-execucao.schema.json` e `SKILL.md`: obediência estrita às Leis #1 (Determinismo), #2 (Saída Binária), #5 (Zero Stubs/TODOs) e validação pelo gate `gates/G_PIPELINE_HANDOFF.py`.
- **D2. Input e Gatilhos:** Interface via CLI determinística `python ecossistema.py run-plan <plano>` e `python ecossistema.py pipeline --handoff <json>` com suporte a `--dry-run` e `--no-exec`.
- **D3. Raio de Impacto e Isolamento:** Isolamento total em branches `task/<task_id>` e diretórios `.worktrees/<task_id>`, garantindo que o branch de trabalho base não receba alterações até aprovação na barreira.
- **D4. Componentes e Fractalidade:** Implementação modular em `tools/aidd-runner/src/` e `scripts/compilador_plano_evolucao.py`, integrada unificadamente na CLI raiz `ecossistema.py`.

### Fase 2: O Chão de Fábrica (Workflow Agêntico)
- **D5. Visão e Escopo:** Executar fatias verticais e tickets de implementação de forma concorrente em ambientes isolados com integração contínua e sem drift.
  - **[Estágio 1 - Compilação de Handoff] D6. O que o Estágio Faz:** Compila o plano Markdown em manifesto JSON estruturado.
  - **[Estágio 1 - Compilação de Handoff] D7. O que o Estágio Recebe:** Diretório de plano em `docs/planos/`.
  - **[Estágio 1 - Compilação de Handoff] D8. O que o Estágio Processa:** Parser de tickets e validação contra schema JSON.
  - **[Estágio 1 - Compilação de Handoff] D9. O que o Estágio Entrega:** Arquivo `handoff_evolution.json`.
  - **[Estágio 2 - Despacho em Worktrees] D6. O que o Estágio Faz:** Cria worktrees paralelas e executa testes/comandos de cada tarefa.
  - **[Estágio 2 - Despacho em Worktrees] D7. O que o Estágio Recebe:** Manifesto de execução.
  - **[Estágio 2 - Despacho em Worktrees] D8. O que o Estágio Processa:** Processos concorrentes e asserção de exit codes locais.
  - **[Estágio 2 - Despacho em Worktrees] D9. O que o Estágio Entrega:** Branches locais validados.
  - **[Estágio 3 - Barreira e Merge] D6. O que o Estágio Faz:** Executa o merge sequencial ou aborta tudo em falhas.
  - **[Estágio 3 - Barreira e Merge] D7. O que o Estágio Recebe:** Status de todas as tarefas paralelas.
  - **[Estágio 3 - Barreira e Merge] D8. O que o Estágio Processa:** Verificação da barreira, merge linear e limpeza física das worktrees.
  - **[Estágio 3 - Barreira e Merge] D9. O que o Estágio Entrega:** Árvore principal consolidada e limpa.
- **D10. Orquestração e Topologia:** Topologia Fork-Join procedural determinística com barreira atômica de sincronização.

### Fase 3: Resiliência e Economia (Engenharia Operacional)
- **D11. Tratamento de Exceções e Fallback:** Abort completo e automático em falha de qualquer task (`git merge --abort`), seguido de limpeza física via `git worktree remove --force` em bloco `finally`.
- **D12. Observabilidade e Frugalidade:** Execução síncrona com logs isolados por task, sem consumo de LLM na orquestração de infraestrutura Git.

### Fase 4: O Inspetor e a Expedição (Validação)
- **D13. Quality Gates (Portões):** Portão binário `gates/G_PIPELINE_HANDOFF.py` validando o manifesto antes da execução, acrescido de barreira de gates pós-merge.
- **D14. Critério de Rejeição (Rollback):** Qualquer erro em task paralela aciona rollback completo descartando os branches de tarefa e restaurando o estado original.
- **D15. Output Consolidado e Handoff:** Manifesto `handoff_evolution.json` validado e árvore Git limpa sem worktrees residuais.

---

## 3. Matriz de Avaliação da Execução
- [x] A ferramenta isolou seu raio de impacto corretamente? Sim, isolamento total em `.worktrees/`.
- [x] O workflow seguiu as fases sem alucinações de LLM em tarefas mecânicas? Sim, motor 100% determinístico em Python e Git.
- [x] O output final passou em todos os Quality Gates e emitiu o Handoff? Sim, validado por `G_PIPELINE_HANDOFF.py` com exit 0.
