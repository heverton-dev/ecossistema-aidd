---
name: aidd-orca
description: Executes multi-phase ORCA plans using isolated Git worktrees and quality gates.
---

# AIDD ORCA — Orquestrador de Planos em Worktrees

Esta skill orquestra a execução automatizada de planos fatiados (`00-PROCESSO-E-DECISOES.md` + `NN-*.md`) em qualquer projeto utilizando worktrees efêmeras e validação estrita de quality gates.

## Capacidades

- **Parser Determinístico de Planos:** interpreta pastas de planos com frentes paralelas.
- **Ciclo de Vida Efêmero de Worktree:** isolamento estrito via `git worktree` e branches efêmeras.
- **Hooks Reativos (Zero Polling):** sinalização por eventos push e sincronismo de estado.
- **Auditoria de Gates Locais:** validação estrita (exit 0) antes de qualquer merge.
- **Circuit Breaker Anti-Loop:** proteção ativa contra travamento ou tempo excessivo.

## Como Usar

Via CLI Central:
```bash
python ecossistema.py orchestrate docs/planos/<plano> --ambiente gitworktree
```
