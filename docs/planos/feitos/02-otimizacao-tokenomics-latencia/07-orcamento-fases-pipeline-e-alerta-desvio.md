# Item 7 — orcamento-fases-pipeline-e-alerta-desvio

> **Escopo:** Estabelecer tabela formal de orcamento de tokens por fase no _pipeline_state.json com alerta explicito de desvio superior a 20% e correcao da alegacao de marketing em pipeline_completo.py.
> **Status:** [EM EXECUCAO]

---

## Contexto ja investigado

- O pipeline possui telemetria (estimar_tokens_tiktoken), mas nao possui metas orcamentarias formais nem alertas estruturados para vazamento de contexto.
- pipeline_completo.py:110-115 contem alegacao de marketing sem baseline medido ('Reducao de >65% no consumo de tokens vs carregamento eager'), violando a Regra #9.

## Definicao de Pronto

1. Adicionar schema de token_budgets por fase na configuracao do pipeline (tools/aidd-generator/config/token_budgets.json).
2. Gravar no _pipeline_state.json o comparativo tokens_utilizados vs orcamento_fase.
3. Emitir alerta estruturado caso uma fase exceda o orcamento em mais de 20%.
4. Corrigir o comentario de marketing em pipeline_completo.py para declaracao tecnica objetiva.

## Criterio de saida

- Orcamento formal auditavel registrado no estado do pipeline.
- Comentarios em conformidade com o gate G_HONESTIDADE_ROTULO.py.
- Testes passando 100%.

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

`
Voce vai implementar o Item 7: orcamento-fases-pipeline-e-alerta-desvio.
1. Crie tools/aidd-generator/config/token_budgets.json com limites de tokens por fase.
2. Atualize o registro de telemetria no _pipeline_state.json para alertar desvios > 20%.
3. Remova a alegacao de 65% em pipeline_completo.py substituindo por descricao tecnica auditavel.
4. Execute python gates/G_HONESTIDADE_ROTULO.py e pytest tools/aidd-generator/tests/ garantindo exit 0.
`

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

`
You are going to implement Item 7: orcamento-fases-pipeline-e-alerta-desvio.
1. Establish tools/aidd-generator/config/token_budgets.json defining per-phase token thresholds.
2. Update pipeline telemetry in _pipeline_state.json to emit structured warnings when budget is exceeded by > 20%.
3. Refactor the unverified 65% marketing claim in pipeline_completo.py to an objective technical docstring.
4. Run python gates/G_HONESTIDADE_ROTULO.py and pytest tools/aidd-generator/tests/ ensuring exit 0.
`
