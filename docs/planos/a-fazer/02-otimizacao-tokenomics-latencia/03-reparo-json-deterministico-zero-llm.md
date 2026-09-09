# Item 3 — reparo-json-deterministico-zero-llm

> **Escopo:** Construir uma escada de reparo JSON deterministica sem uso de LLM em utils_delegacao.py, eliminando retries caros de LLM quando respostas contem pequenas quebras de formatacao JSON.
> **Status:** [RASCUNHO — Aguardando Aprovacao Humana]

---

## Contexto ja investigado

- utils_delegacao.py:248 aciona _validar_pydantic_com_retry(max_retries=3). Quando o JSON quebra, reenvia a resposta crua de volta ao modelo ate 3 vezes.
- A funcao _extrair_json_manual ja resolve parte das quebras, mas ainda recorre ao LLM para erros simples como virgulas sobrando, trailing quotes ou markdown fences mal fechados.

## Definicao de Pronto

1. Integrar escada deterministica de normalizacao JSON antes de qualquer retry LLM:
   - Extracao manual de fences e substrings.
   - Limpeza de virgulas trailing em arrays/objetos via regex deterministico.
   - Sanitizacao de quebras de linha em literais string.
2. Reduzir os retries de LLM em _validar_pydantic_com_retry para no maximo 1 tentativa com mensagem estruturada do erro, apenas se a escada deterministica falhar.
3. Teste unitario com fixture de 10 payloads JSON sinteticamente malformados comprovando >= 8 recuperacoes sem chamada de LLM.

## Criterio de saida

- Zero chamadas LLM para erros comuns de formatacao JSON.
- Teste de mutacao com payloads quebrados passando com sucesso.

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

`
Voce vai implementar o Item 3: reparo-json-deterministico-zero-llm.
1. Em tools/aidd-generator/scripts/utils_delegacao.py:
   - Aprimore a extracao deterministica de JSON com limpeza mecanica (trailing commas, quotes soltas).
   - Diminua as tentativas de retry LLM para no maximo 1 (apenas pos-falha mecanica).
2. Crie testes em tools/aidd-generator/tests/test_reparo_json.py validando recuperacao sem rede/LLM.
3. Garanta exit 0 em pytest tools/aidd-generator/tests/.
`

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

`
You are going to implement Item 3: reparo-json-deterministico-zero-llm.
1. In tools/aidd-generator/scripts/utils_delegacao.py:
   - Enhance deterministic JSON extraction with mechanical repairs (trailing commas, unbalanced quotes).
   - Restrict LLM retries in _validar_pydantic_com_retry to at most 1 attempt after mechanical failure.
2. Add tests in tools/aidd-generator/tests/test_reparo_json.py testing repair without LLM invocation.
3. Ensure exit 0 in pytest tools/aidd-generator/tests/.
`
