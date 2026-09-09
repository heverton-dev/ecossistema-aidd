# Item 5 — contrato-formal-schema-ops-para-master-enterprise

> **Escopo:** Formalizar o contrato de integração comprovado nº 1 (ops -> master/enterprise) através de um JSON Schema versionado para o PLANO-INFRAESTRUTURA.json e um Quality Gate de validação.
> **Status:** [RASCUNHO — Aguardando Aprovação Humana]

---

## Contexto já investigado

- O dimensionamento real do aidd-ops gera PLANO-INFRAESTRUTURA.json, que é consumido por scaffold_infra.py em master e enterprise.
- Essa integração opera por convenção implícita sem validação de schema nem contrato formal versionado.

## Definição de Pronto

1. Definir o schema formal versionado componentes/compartilhado/specs/plano-infraestrutura.schema.json.
2. Validar que o gerador de sizing do ops emite artefatos 100% aderentes a esse schema via jsonschema.
3. Adicionar validação de schema no leitor de scaffold_infra.py antes de aplicar os resources no Helm/Compose.
4. Criar teste de contrato automatizado garantindo interoperabilidade contínua.

## Critério de saída

- Schema JSON documentado e versionado.
- Validação ativa no aidd-ops e no leitor do master/enterprise.
- Testes de integração de contrato com exit 0.

## Prompt de Execução (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

`
Você vai implementar o Item 5: contrato-formal-schema-ops-para-master-enterprise.
1. Crie componentes/compartilhado/specs/plano-infraestrutura.schema.json.
2. Adicione validação determinística via jsonschema na geração do PLANO-INFRAESTRUTURA.json no aidd-ops.
3. Adicione validação no consumidor scaffold_infra.py em master/enterprise.
4. Crie teste de contrato em pytest verificando a interoperabilidade.
`

## Prompt de Execução — English version

> Copy the block below in full to the executor agent:

`
You are going to implement Item 5: contrato-formal-schema-ops-para-master-enterprise.
1. Create componentes/compartilhado/specs/plano-infraestrutura.schema.json.
2. Add jsonschema validation to ops sizing output.
3. Validate schema in scaffold_infra.py consumer in master and enterprise.
4. Add contract test ensuring end-to-end compatibility.
`
