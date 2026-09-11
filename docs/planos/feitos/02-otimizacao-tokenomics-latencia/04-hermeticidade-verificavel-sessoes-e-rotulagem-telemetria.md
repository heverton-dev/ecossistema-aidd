# Item 4 — hermeticidade-verificavel-sessoes-e-rotulagem-telemetria

> **Escopo:** Garantir hermeticidade real na invocacao headless de harnesses CLI e adicionar rotulagem transparente de telemetria no modo delegado (Regra #9 de honestidade de rotulo).
> **Status:** [EM EXECUCAO]

---

## Contexto ja investigado

- solicitar_llm_modo_headless monta comandos CLI para subagentes, mas nao audita se o harness esta executando com flags de sessao limpa [TK-6].
- No modo delegado (solicitar_llm_modo_delegado), o modelo e acionado dentro da sessao ativa da conversa, gerando contaminacao de contexto acumulado nao reportada na telemetria.

## Definicao de Pronto

1. Adicionar validacao/flags explicitas de sessao limpa (--no-session-persistence, sessoes efemeras) ao montar comandos em solicitar_llm_modo_headless.
2. Criar Quality Gate AST garantindo que nenhum executor headless dispare processos sem flag de isolamento.
3. Na telemetria de tokens (utils_delegacao.py), rotular explicitamente se a medicao veio de sessao_isolada ou sessao_compartilhada_delegada.

## Criterio de saida

- Comandos headless auditados por gate para sessoes efemeras.
- Telemetria de tokens honesta e categorizada por tipo de sessao.

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

`
Voce vai implementar o Item 4: hermeticidade-verificavel-sessoes-e-rotulagem-telemetria.
1. Audite e garanta flags de sessao isolada em solicitar_llm_modo_headless.
2. Adicione categoria sessao_compartilhada na telemetria de utils_delegacao.py quando rodar no modo delegado.
3. Adicione assercoes no gate de execucao de subagente verificando a hermeticidade.
4. Execute pytest tools/aidd-generator/tests/ com exit 0.
`

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

`
You are going to implement Item 4: hermeticidade-verificavel-sessoes-e-rotulagem-telemetria.
1. Enforce ephemeral/clean session flags in solicitar_llm_modo_headless.
2. Differentiate sessao_compartilhada vs sessao_isolada in delegation telemetry metadata.
3. Add AST verification for clean session arguments in CLI invocation.
4. Run pytest tools/aidd-generator/tests/ with exit 0.
`
