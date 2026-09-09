# Item 9 — trazer-deliverables-generator-perimetro-gates

> **Escopo:** Conectar a Fase 8 do aidd-generator e o processo de geração autônoma ao perímetro de Quality Gates do ecossistema, garantindo validação arquitetural estática no código gerado.
> **Status:** [RASCUNHO — Aguardando Aprovação Humana]

---

## Contexto já investigado

- O código gerado pela Fase 8 do generator vive fora da validação de gates do monorepo; a conformidade depende apenas de prompts e testes da própria fase gerada.
- Risco de regressão e entrega de código sem separação de camadas.

## Definição de Pronto

1. Atualizar as instruções do micro-ambiente de prompt da Fase 08 (AGENTS.md da fase) para exigir explicitamente o blueprint de Clean Architecture & DDD.
2. Acoplar a execução de G_ARQUITETURA_DELIVERABLE.py na etapa de verificação de gates da Fase 08 (erificar_gates.py).
3. Fazer o pipeline falhar ou acionar ciclo de autocorreção caso a Fase 08 produza vazamento de SQL ou modelos anêmicos.
4. Validar execução em teste de fumaça (dry-run) do pipeline do generator.

## Critério de saída

- Fase 08 valida arquitetura do produto gerado contra Quality Gate formal.
- Pipeline rejeita código gerado que viole a Dependency Rule.

## Prompt de Execução (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

`
Você vai implementar o Item 9: trazer-deliverables-generator-perimetro-gates.
1. No aidd-generator, integre o gate G_ARQUITETURA_DELIVERABLE.py dentro da verificação da Fase 08.
2. Atualize o prompt/micro-ambiente da Fase 08 para orientar a geração no modelo Clean Architecture + DDD.
3. Assegure que violações arquiteturais no código gerado sejam reportadas e corrigidas no loop de autocorreção.
4. Execute os testes do aidd-generator garantindo aprovação.
`

## Prompt de Execução — English version

> Copy the block below in full to the executor agent:

`
You are going to implement Item 9: trazer-deliverables-generator-perimetro-gates.
1. In aidd-generator, integrate G_ARQUITETURA_DELIVERABLE.py into Phase 08 gate verification.
2. Update Phase 08 prompt instructions to enforce the Clean Architecture & DDD blueprint.
3. Ensure architectural violations in generated code trigger the self-correction loop.
4. Run aidd-generator tests and ensure pass.
`
