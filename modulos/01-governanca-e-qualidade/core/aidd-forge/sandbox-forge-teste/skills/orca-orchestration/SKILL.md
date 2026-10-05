---
name: orca-orchestration
description: Orquestracao multi-agente no ORCA ADE — worktrees isoladas por worker, roteamento por especialidade e decision gates para tarefas sensiveis.
---

# Orca Orchestration — Multi-Agente com Isolamento

## Objetivo

Coordenar multiplos workers (arquiteto, database, frontend, seguranca)
em worktrees Git isoladas, com fallback em cascata quando o host tem
apenas um agente disponivel.

## Worktrees por Worker

- Cada worker roda em `git worktree` proprio: nenhum worker enxerga
  arquivos de outro em progresso.
- Worktree e destruida (ou mergeada) ao final da tarefa do worker —
  nunca deixar worktrees orfas.

## Roteamento por Especialidade

- Se o host tem multiplos agentes (`claude`, `codex`, `cursor`,
  `antigravity`), rotear por especialidade:
  - Arquitetura/planejamento -> agente configurado como arquiteto.
  - Schemas/queries/migrations -> agente configurado como database.
- Se o host tem apenas 1 agente, todos os workers usam esse agente,
  mantendo isolamento via worktree (Modo "Agente Unico Isolado").

## Decision Gates

- Toda tarefa que toca schema de banco de dados, segredo ou
  configuracao de seguranca **para** antes de aplicar e aguarda
  aprovacao explicita (decision gate) — nunca aplica automaticamente.
- Registrar cada decision gate disparado (tarefa, motivo, decisao) para
  auditoria posterior.

## Gate de Saida

`exit 0` somente se todo worker finalizou em sua worktree isolada, sem
worktrees remanescentes, e nenhum decision gate pendente ficou sem
resposta.
