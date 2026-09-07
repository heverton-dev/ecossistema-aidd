# Comando /orchestrate

Dispara a orquestração multi-agente ORCA ADE para o plano especificado ou plano local.

## Uso:
`/orchestrate [caminho_do_plano]`

## Ação:
Executa a skill `orca-plan-orchestrator` para compilar o Plano de Voo, criar worktrees efêmeras, executar frentes em paralelo com hooks reativos e realizar o merge apenas após aprovação dos Quality Gates.

Equivalente CLI: `python ecossistema.py orchestrate [caminho_do_plano]`
Modo seguro (Plano de Voo apenas): `python ecossistema.py orchestrate [caminho_do_plano] --dry-run`
