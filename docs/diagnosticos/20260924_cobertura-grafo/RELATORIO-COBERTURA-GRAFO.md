# Relatório de Cobertura do Grafo — aidd-diagnose Ticket 3 (D8)

- Repositório: `C:\Users\trcnologia\Desktop\worktrees_evolucao-aidd-diagnose-ciclo-01\Fase_3_Ticket_3_Detec__o_de_Grafo_Desatualizado`
- Data (UTC): 2026-09-24T14:18:41
- `.py` versionados: 1746
- Sessão: `C:\Users\trcnologia\Desktop\worktrees_evolucao-aidd-diagnose-ciclo-01\Fase_3_Ticket_3_Detec__o_de_Grafo_Desatualizado\docs\diagnosticos\20260924_cobertura-grafo`

## Contagens por etapa

| etapa | exit | cobertos | faltantes |
|---|---|---|---|
| antes | None | 0 | 1746 |
| update | 0 | 2 | 1744 |
| build | 0 | 1746 | 0 |

## Causa-raiz

graph.db existia mas estava vazio (0 nós): worktree nova com .code-review-graph/ gitignored nunca recebeu build inicial. O update incremental cobriu parte dos arquivos, mas deixou faltantes (não reparseia inalterados desde HEAD~1); o build completo reduziu a lacuna.

> Nunca reporte '0 impactados' para arquivo sem nós no grafo:
> use `cobertura_grafo.py verificar` antes da Fase 2.
