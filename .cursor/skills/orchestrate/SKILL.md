---
name: orchestrate
description: Orquestrador multi-agente determinístico ORCA ADE para execução de planos com worktrees efêmeras, hooks reativos e gates locais.
---

# /orchestrate — ORCA ADE Plan Orchestrator

Contrato executável universal do slash command /orchestrate [plano].

## Protocolo Interativo do Agente (/orchestrate)
Quando invocado:
1. Valida plano (00-PROCESSO-E-DECISOES.md e NN-*.md).
2. Pergunta modo (Automatizado / Interativo) e harnesses (Global / Miscelânea por frente).
3. Apresenta Plano de Voo (--dry-run).
4. Pede confirmação e executa.
