# tools/ foi extinta (modularização VSA, ciclo-03)

O código de cada ferramenta mora agora numa única pasta em `modulos/` (decisão A do ciclo-03).
Este arquivo fica por 1 ciclo para quem procurar o caminho antigo; sai no ciclo seguinte.

| Pasta antiga | Pasta nova |
|---|---|
| tools/aidd-forge/ | modulos/01-governanca-e-qualidade/core/aidd-forge/ |
| tools/aidd-planner/ | modulos/01-governanca-e-qualidade/core/aidd-planner/ |
| tools/aidd-pure/ | modulos/02-triade-motores/fluxo-01-pure/core/aidd-pure/ |
| tools/aidd-open/ | modulos/02-triade-motores/fluxo-02-open/core/aidd-open/ |
| tools/aidd-freedom/ | modulos/02-triade-motores/fluxo-03-freedom/core/aidd-freedom/ |
| tools/aidd-master/ | modulos/03-plataforma-e-entrega/fatiamento-master/aidd-master/ |
| tools/aidd-enterprise/ | modulos/03-plataforma-e-entrega/blindagem-enterprise/aidd-enterprise/ |
| tools/aidd-ops/ | modulos/03-plataforma-e-entrega/operacoes-ops/aidd-ops/ |

Fonte única do mapa: campo `pasta` de `componentes/compartilhado/specs/MAPA-DONOS-FERRAMENTAS.json`.
Prova de zero perda: `docs/auditoria/modularizacao-vsa/ciclo-03/REMOCAO-TOOLS.md`.
