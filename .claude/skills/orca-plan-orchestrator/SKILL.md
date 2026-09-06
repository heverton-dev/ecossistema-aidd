---
name: orca-plan-orchestrator
description: Orquestrador multi-agente determinístico ORCA ADE para execução paralela de planos fatiados com git worktrees efêmeras, hooks reativos e gates locais.
---

# ORCA ADE — Plan Orchestrator

Esta skill orquestra a execução automatizada de planos fatiados (`00-PROCESSO-E-DECISOES.md` + `NN-*.md`) em qualquer projeto ou repositório.

## Capacidades

- **Parser Determinístico de Planos:** interpreta pastas de planos com frentes paralelas.
- **Ciclo de Vida Efêmero de Worktree:** isolamento estrito via `git worktree` e branches efêmeras.
- **Hooks Reativos (Zero Polling):** sinalização por eventos push e sincronismo de estado.
- **Auditoria de Gates Locais:** validação estrita (exit 0) antes de qualquer merge.
- **Circuit Breaker Anti-Loop:** proteção ativa contra travamento ou excesso de tempo/inatividade.
- **CLI e Plano de Voo:** compilação de comandos de harness e visualização via `--dry-run`.

## Slash Command

`/orchestrate [plano]`

## Uso via CLI

```bash
# Visualizar plano de voo sem executar (Zero LLM / Zero Token)
python ecossistema.py orchestrate [plano] --dry-run

# Executar com harness específico
python ecossistema.py orchestrate [plano] --harness mimo
```
