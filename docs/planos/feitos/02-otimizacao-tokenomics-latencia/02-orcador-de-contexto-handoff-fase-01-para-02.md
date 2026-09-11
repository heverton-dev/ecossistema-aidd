# Item 2 — orcador-de-contexto-handoff-fase-01-para-02

> **Escopo:** Implementar poda deterministica e selecao top-k com campos seletos no handoff de referencias entre a Fase 1 (Pesquisador) e a Fase 2 (Analisador), eliminando o dump bruto de JSON.
> **Status:** [EM EXECUCAO]

---

## Contexto ja investigado

- 02_analisador.py serializa a lista completa de referencias via json.dumps(referencias, indent=2), despejando dezenas de milhares de tokens desnecessarios de metadados [TK-1].
- A Fase 1 ja calcula scores de relevancia (R1-R4) que podem ser reutilizados para selecao das top referencias.

## Definicao de Pronto

1. Criar funcao de poda e orcamento montar_handoff_referencias(referencias, max_tokens) em 02_analisador.py.
2. Filtrar apenas campos essenciais para analise (titulo, resumo, URL, relevancia, dependencias-chave) descartando metadados inflados.
3. Selecionar top-k referencias com base no ranking da Fase 1, respeitando um teto orcamentario explicito.
4. Adicionar cabecalho informativo indicando total de referencias avaliadas vs podadas.

## Criterio de saida

- Handoff para a Fase 2 consome <= 5.000 tokens mesmo com 30+ referencias brutas na entrada.
- Teste unitario comprovando integridade dos campos essenciais apos a poda.

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

`
Voce vai implementar o Item 2: orcador-de-contexto-handoff-fase-01-para-02.
1. Em tools/aidd-generator/scripts/phases/02_analisador.py:
   - Substitua o dump integral json.dumps(referencias) por um seletor top-k com campos essenciais.
   - Aplique teto de orcamento de tokens para entrada da Fase 2.
2. Crie teste automatizado demonstrando que para um payload de 30 referencias grandes, o handoff se mantem abaixo do orcamento configurado.
3. Rode pytest tools/aidd-generator/tests/ com exit 0.
`

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

`
You are going to implement Item 2: orcador-de-contexto-handoff-fase-01-para-02.
1. In tools/aidd-generator/scripts/phases/02_analisador.py:
   - Replace full json.dumps(referencias) with top-k selection and essential fields filtering.
   - Enforce an explicit token budget ceiling for Phase 2 input.
2. Add automated unit test proving that a 30-reference raw payload stays strictly under the token ceiling.
3. Run pytest tools/aidd-generator/tests/ with exit 0.
`
