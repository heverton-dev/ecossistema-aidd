# Item 5 — middleware-compressao-sandeco-token-reduce

> **Escopo:** Integrar a skill sandeco-token-reduce como middleware opcional de pipeline para compressao de handoffs de prosa longa (Fase 1->2 e documentacao), com preflight de verificacao e fallback deterministico.
> **Status:** [RASCUNHO — Aguardando Aprovacao Humana]

---

## Contexto ja investigado

- A skill sandeco-token-reduce (LLMLingua-2) existe e esta sincronizada em 6 harnesses, mas atua apenas de forma conversacional manual.
- Pode gerar economia de ~10-12k tokens por execucao em handoffs de texto longo sem tocar em codigo nem quebrar schemas.

## Definicao de Pronto

1. Criar interface em Python para acionar a compressao de sandeco-token-reduce a partir de scripts do generator (compressor_middleware.py).
2. Adicionar verificacao de prontidao no preflight_llm: se LLMLingua-2 estiver disponivel, usa; se nao, segue com fallback deterministico transparente.
3. Definir politica estrita: comprimir SOMENTE prosa descritiva (resumos de referencias, narrativas da fase 6). NUNCA comprimir codigo nem JSON de schema.
4. Registrar o uso da compressao e a taxa real obtida na telemetria de execucao.

## Criterio de saida

- Pipeline executa normalmente com ou sem o compressor instalado (resiliencia total).
- Quando ativado, reduz >= 40% dos caracteres de prosa em handoffs marcados como compressiveis.

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

`
Voce vai implementar o Item 5: middleware-compressao-sandeco-token-reduce.
1. Crie adaptador em tools/aidd-generator/scripts/compressor_middleware.py conectado a skill sandeco-token-reduce.
2. Configure politica declarativa que restringe compressao a texto livre/prosa.
3. Adicione fallback deterministico e medicao de economia em telemetria.
4. Execute pytest tools/aidd-generator/tests/ com exit 0.
`

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

`
You are going to implement Item 5: middleware-compressao-sandeco-token-reduce.
1. Create adapter tools/aidd-generator/scripts/compressor_middleware.py integrating sandeco-token-reduce.
2. Apply strict declarative policy restricting compression to prose/free text.
3. Implement deterministic fallback when compressor is uninitialized and log token delta.
4. Run pytest tools/aidd-generator/tests/ with exit 0.
`
