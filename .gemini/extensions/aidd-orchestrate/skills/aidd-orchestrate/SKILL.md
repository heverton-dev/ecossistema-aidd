---
name: aidd-orchestrate
description: Routes plan execution between ORCA app, agent worktrees, and native execution engines.
---

# AIDD Orchestrate — Roteador de Execução (/orchestrate)

Contrato executável universal do comando `/orchestrate <plano>`. Conduz a montagem do Plano de Voo e a escolha do ambiente de execução (ORCA ADE, Git Worktrees efêmeras ou Subagentes).

## Como Usar

No chat do assistente:
```text
/orchestrate <caminho_do_plano>
```

Via CLI Central:
```bash
python ecossistema.py orchestrate docs/planos/<nome> [--dry-run]
```
