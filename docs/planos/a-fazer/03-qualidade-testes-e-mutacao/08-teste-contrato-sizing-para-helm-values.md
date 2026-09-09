# Item — teste-contrato-sizing-para-helm-values

> **Escopo:** Criar teste de contrato automatizado para o elo comprovado ops -> master/enterprise, verificando que o sizing de PLANO-INFRAESTRUTURA.json é refletido com exatidão no values.yaml do Helm.
> **Status:** [RASCUNHO — Aguardando Aprovação Humana]

---

## Contexto já investigado

- O elo ops -> Helm não possui teste ponta a ponta que verifique se os recursos calculados são escritos exatamente no chart gerado.

## Definição de Pronto

1. Criar teste que executa sizing do ops gerando fixture.
2. Executar scaffold_infra.py consumindo fixture.
3. Afirmar recursos idênticos no values.yaml.

## Critério de saída

- Teste de contrato ponta a ponta ops->enterprise aprovado.
- Testes reais passando sem stubs falsos.
- Gates de integridade aprovados.

## Prompt de Execução (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Você vai implementar o Item: teste-contrato-sizing-para-helm-values.
Siga rigorosamente a Definição de Pronto acima:
1. Criar teste que executa sizing do ops gerando fixture.
2. Executar scaffold_infra.py consumindo fixture.
3. Afirmar recursos idênticos no values.yaml.
Garanta exit 0 nos testes e gates pertinentes.
```

## Prompt de Execução — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item: teste-contrato-sizing-para-helm-values.
Strictly follow the Definition of Done above:
1. Criar teste que executa sizing do ops gerando fixture.
2. Executar scaffold_infra.py consumindo fixture.
3. Afirmar recursos idênticos no values.yaml.
Ensure exit code 0 across relevant tests and gates.
```
