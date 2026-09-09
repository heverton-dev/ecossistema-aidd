# Item — testes-exatidao-sizing-ops-fixtures-ouro

> **Escopo:** Substituir asserções de piso (>= 2) no dimensionamento de infraestrutura do aidd-ops por fixtures de ouro com soma aritmética exata e arredondamento por nicho.
> **Status:** [RASCUNHO — Aguardando Aprovação Humana]

---

## Contexto já investigado

- test_pipeline_ops.py usa asserts de piso (>= 2) [TS-3]. math.ceil determinístico deve ser validado com valores exatos.

## Definição de Pronto

1. Criar fixture de ouro com requisitos exatos esperados por nicho.
2. Substituir >= por == nos asserts de vCPU e RAM.
3. Validar cálculo determinístico.

## Critério de saída

- Testes de sizing afirmam valores exatos de vCPU e memória.
- Testes reais passando sem stubs falsos.
- Gates de integridade aprovados.

## Prompt de Execução (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Você vai implementar o Item: testes-exatidao-sizing-ops-fixtures-ouro.
Siga rigorosamente a Definição de Pronto acima:
1. Criar fixture de ouro com requisitos exatos esperados por nicho.
2. Substituir >= por == nos asserts de vCPU e RAM.
3. Validar cálculo determinístico.
Garanta exit 0 nos testes e gates pertinentes.
```

## Prompt de Execução — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item: testes-exatidao-sizing-ops-fixtures-ouro.
Strictly follow the Definition of Done above:
1. Criar fixture de ouro com requisitos exatos esperados por nicho.
2. Substituir >= por == nos asserts de vCPU e RAM.
3. Validar cálculo determinístico.
Ensure exit code 0 across relevant tests and gates.
```
