---
name: aidd-pipeline-runner
description: Executa pipelines determinísticos da Tríade em Git Worktrees efêmeras com barreira de sincronização (Join Barrier) a partir de planos Markdown ou manifestos JSON.
---

# AIDD Pipeline Runner — Motor Determinístico de Execução da Tríade Canônica

Esta skill executa o pipeline determinístico em Git Worktrees efêmeras com Barreira de Sincronização (Join Barrier) e Fases Sequenciais Síncronas, assegurando conformidade absoluta com as leis do ecossistema.

## Invariantes e Leis Auditadas

1. **Determinismo First (Lei #1):** Despacho estrito baseado em JSON Schema formal (`handoff-execucao.schema.json`) e operações nativas do Git.
2. **Saída Binária (Lei #2):** `exit 0` = sucesso completo de todas as validações; `exit 1` = bloqueio imediato e aborto de merge.
3. **Zero Stubs (Lei #5):** Rejeição mecânica de TODO, FIXME, PLACEHOLDER e comandos de validação triviais (`exit 0`, `true`, `echo ok`).
4. **Supremacia Agnóstica (Lei #6):** Operação 100% multiplataforma (Windows PowerShell e Linux Bash) distribuída indistintamente por todos os 7 harnesses.
5. **Desenvolvedor no Controle (Lei #7):** Execução síncrona com inspeção total, sem subagentes invisíveis ou caixas-pretas. Isolamento total em worktrees limpas deterministicamente no encerramento.

## Arquitetura do Pipeline

```text
Plano Markdown (docs/planos/) OU Manifesto JSON de Handoff
                     │
                     ▼
┌────────────────────────────────────────────────────────┐
│ Fase Paralela Assíncrona (Git Worktrees Efêmeras)     │
│  - Task A (.worktrees/TASK-A na branch task/TASK-A)    │
│  - Task B (.worktrees/TASK-B na branch task/TASK-B)    │
│  - Execução paralela de comandos de validação          │
└────────────────────────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────┐
│ Barreira de Sincronização (Join Barrier)               │
│  - Se qualquer task falhar: aborto total e cleanup     │
│  - Se todas passarem: merge sequencial na branch base  │
└────────────────────────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────┐
│ Fase Sequencial Síncrona                               │
│  - Execução ordenada na árvore principal               │
│  - Migrações, gates globais e validação final          │
└────────────────────────────────────────────────────────┘
```

## Como Usar

### 1. A partir de um Plano Markdown (`run-plan`)
Compila tickets estruturados em `docs/planos/` para JSON e executa o pipeline completo:
```bash
python ecossistema.py run-plan docs/planos/a-fazer/PLAN-0029-teste-e2e-ferramentas
```
Para simulação sem escrita no repositório:
```bash
python ecossistema.py run-plan PLAN-0029-teste-e2e-ferramentas --dry-run
```
Para compilar apenas o handoff sem executar:
```bash
python ecossistema.py run-plan PLAN-0029-teste-e2e-ferramentas --no-exec
```

### 2. A partir de um Manifesto JSON de Handoff (`pipeline`)
Executa o motor de worktrees diretamente sobre manifesto formal validado:
```bash
python ecossistema.py pipeline --handoff docs/planos/a-fazer/PLAN-0029-teste-e2e-ferramentas/handoff_evolution.json
```
Para simular em modo silencioso:
```bash
python ecossistema.py pipeline --handoff docs/planos/a-fazer/PLAN-0029-teste-e2e-ferramentas/handoff_evolution.json --dry-run -q
```

### 3. Via Slash Commands
Em qualquer harness (Claude, Antigravity, OpenCode, Cursor, etc.):
- `/run-plan <plano>` -> Intercepta e dispara `python ecossistema.py run-plan <plano>`.
- `/pipeline <handoff>` -> Intercepta e dispara `python ecossistema.py pipeline --handoff <handoff>`.
