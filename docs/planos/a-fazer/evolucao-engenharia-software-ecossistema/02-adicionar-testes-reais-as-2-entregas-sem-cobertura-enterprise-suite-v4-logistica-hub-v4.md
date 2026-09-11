# Item 2 — Adicionar testes reais as 2 entregas sem cobertura (enterprise-suite-v4, logistica-hub-v4)

> **Escopo:** Criar suite de testes real (nao superficial) para as duas entregas em `tools/aidd-enterprise/materiais-extras/examples/` que hoje nao tem pasta `tests/`: `enterprise-suite-v4` e `logistica-hub-v4`. Nao inclui as outras 11 entregas do catalogo, que ja tem testes (ainda que finos).
> **Status:** [APROVADO — Aguardando Execucao]
> **Nota Atual (0-10):** 2.0 — evidencia: ls tests/ ausente em tools/aidd-enterprise/materiais-extras/examples/enterprise-suite-v4 e logistica-hub-v4; testes de exemplo finos (test_catalogo.py 55 linhas, test_platform.py 48 linhas)
> **Nota Alvo (0-10):** 9.0
> **Nota Real (pos-implementacao):** [Pendente - preencher somente apos o fechamento real deste item/iniciativa, via o mesmo mecanismo que mediu a Nota Atual]

---

## Contexto ja investigado

- 13 entregas ao todo em tools/aidd-enterprise/materiais-extras/examples/; 2 sem `tests/` nenhum: enterprise-suite-v4 e logistica-hub-v4.
- As entregas que tem testes, tem testes finos (ex.: test_catalogo.py com 55 linhas, test_platform.py com 48 linhas) — referencia de tamanho minimo aceitavel hoje, nao o alvo ideal.

## Definicao de Pronto

1. `tools/aidd-enterprise/materiais-extras/examples/enterprise-suite-v4/tests/` criado com testes reais cobrindo os fluxos principais da entrega.
2. `tools/aidd-enterprise/materiais-extras/examples/logistica-hub-v4/tests/` criado com testes reais cobrindo os fluxos principais da entrega.
3. `pytest` roda com exit 0 nas duas pastas novas, sem stubs/mocks disfarcados de teste.

## Criterio de saida

- As duas entregas passam a ter `tests/` com pelo menos a mesma cobertura de fluxo que as outras 11 entregas do catalogo.
- Testes rodados de verdade (pytest real, exit 0), nao apenas criados.

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai implementar o Item 2: Adicionar testes reais as 2 entregas sem cobertura (enterprise-suite-v4, logistica-hub-v4).
Siga rigorosamente a Definicao de Pronto acima.
Nao invente aprovacoes e mantenha as regras do monorepo.
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 2: Adicionar testes reais as 2 entregas sem cobertura (enterprise-suite-v4, logistica-hub-v4).
Strictly follow the Definition of Done above.
Do not fabricate approvals and maintain monorepo governance rules.
```
