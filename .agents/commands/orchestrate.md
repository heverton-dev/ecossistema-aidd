# Comando /orchestrate (etapa 3 de 3)

> **Fluxo unico (3 etapas, cada uma para pra decisao do usuario):** `/melhoria` -> `/plan` -> `/orchestrate`. Nenhuma dispara a seguinte sozinha.

Dispara a orquestração multi-agente ORCA ADE para o plano especificado ou plano local.

## Uso:
`/orchestrate [caminho_do_plano]`

## Ação:
Executa a skill `orchestrate` (dona unica deste comando): pergunta o ambiente (ORCA / Subagentes / Git Worktree nativo), compila o Plano de Voo, pede aprovacao e so entao executa as frentes, com merge apenas apos aprovacao dos Quality Gates. Na via Git Worktree nativo ela aciona a skill-motor `orca-plan-orchestrator`; na via ORCA, segue o manual da versao instalada (`orca skills get orca-cli`).

Equivalente CLI: `python ecossistema.py orchestrate [caminho_do_plano]`
Modo seguro (Plano de Voo apenas): `python ecossistema.py orchestrate [caminho_do_plano] --dry-run`
