# Item 2 — unificar-orquestradores-generator-e-ops

> **Escopo:** Eliminar orquestradores concorrentes/duplicados no aidd-generator (pipeline_completo vs pipeline_prefect) e no aidd-ops (pipeline_ops vs pipeline_ops_deploy), estabelecendo uma fonte única de orquestração por ferramenta.
> **Status:** [RASCUNHO — Aguardando Aprovação Humana]

---

## Contexto já investigado

- 	ools/aidd-generator/scripts/pipeline_completo.py (393 linhas) e pipeline_prefect.py (344 linhas) implementam o mesmo fluxo de 8 fases.
- 	ools/aidd-ops/scripts/pipeline_ops.py (789 linhas) e pipeline_ops_deploy.py (352 linhas) repetem lógica de orquestração em vez de compor fases.

## Definição de Pronto

1. Eleger um único orquestrador canônico para o aidd-generator (mantendo execução determinística e suporte a fases 1 a 8).
2. Deprecar formalmente ou remover o arquivo orquestrador secundário, garantindo que a CLI do generator e a UI apontem para a fonte única.
3. Consolidar no aidd-ops a orquestração de deploy como extensão modular do pipeline principal.
4. Garantir que os testes de integração de ambas as ferramentas passem 100%.

## Critério de saída

- Apenas 1 orquestrador ativo por pipeline no generator e no ops.
- Pytest de generator e ops com exit 0.

## Prompt de Execução (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

`
Você vai implementar o Item 2: unificar-orquestradores-generator-e-ops.
1. No aidd-generator, unifique pipeline_completo.py e pipeline_prefect.py em um único orquestrador canônico sem duplicidade.
2. No aidd-ops, componha a lógica de deploy dentro do fluxo de pipeline sem manter arquivos concorrentes.
3. Atualize os pontos de entrada na CLI e web runners para referenciar a fonte única.
4. Execute os testes:
   - pytest tools/aidd-generator/tests/
   - pytest tools/aidd-ops/tests/
Garanta exit 0.
`

## Prompt de Execução — English version

> Copy the block below in full to the executor agent:

`
You are going to implement Item 2: unificar-orquestradores-generator-e-ops.
1. In aidd-generator, consolidate pipeline_completo.py and pipeline_prefect.py into a single canonical pipeline orchestrator.
2. In aidd-ops, refactor pipeline_ops.py and pipeline_ops_deploy.py to eliminate dual-path orchestration.
3. Ensure CLI routers and web runners invoke the unified pipeline.
4. Run:
   - pytest tools/aidd-generator/tests/
   - pytest tools/aidd-ops/tests/
Ensure exit 0.
`
