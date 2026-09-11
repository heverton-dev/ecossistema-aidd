# Item 3 — Quebrar funcoes gigantes get_swagger_html (736 linhas) e compose_suite (277/273)

> **Escopo:** Decompor as duas funcoes identificadas pelo `code-review-graph` como as maiores do ecossistema: `get_swagger_html` (736 linhas, presente em `enterprise-suite-v4` e `logistica-hub-v4`, `src/core/openapi.py:284`) e `compose_suite` (277/273 linhas, `master`/`enterprise` `scripts/compose_suite.py:407`). Nao inclui `cmd_orchestrate`/`orchestrate_cli` em `ecossistema.py` (239/183 linhas) — identificadas na mesma varredura, mas fora do escopo original deste item; ficam registradas aqui como candidatas a um item futuro.
> **Status:** [EM EXECUCAO]
> **Nota Atual (0-10):** 4.0 — evidencia: code-review-graph find_large_functions: get_swagger_html 736 linhas (enterprise-suite-v4 e logistica-hub-v4 src/core/openapi.py:284), compose_suite 277/273 (master/enterprise scripts/compose_suite.py:407)
> **Nota Alvo (0-10):** 8.0
> **Nota Real (pos-implementacao):** [Pendente - preencher somente apos o fechamento real deste item/iniciativa, via o mesmo mecanismo que mediu a Nota Atual]

---

## Contexto ja investigado

- `code-review-graph find_large_functions` apontou get_swagger_html (736 linhas) e compose_suite (277/273 linhas) como as funcoes monoliticas mais criticas do ecossistema.

## Definicao de Pronto

1. `get_swagger_html` decomposta em funcoes menores por responsabilidade (ex.: montagem de schema, montagem de paths, serializacao final), nas duas entregas onde existe.
2. `compose_suite` decomposta em funcoes menores por responsabilidade, no master e no enterprise.
3. Testes reais existentes continuam passando apos a decomposicao (nenhuma mudanca de comportamento).

## Criterio de saida

- Nenhuma das duas funcoes excede um tamanho razoavel (ex.: sem funcao unica acima de ~100-150 linhas) apos a decomposicao.
- Suite de testes de master/enterprise e das duas entregas passa com exit 0.

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai implementar o Item 3: Quebrar funcoes gigantes get_swagger_html (736 linhas) e compose_suite (277/273).
Siga rigorosamente a Definicao de Pronto acima.
Nao invente aprovacoes e mantenha as regras do monorepo.
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 3: Quebrar funcoes gigantes get_swagger_html (736 linhas) e compose_suite (277/273).
Strictly follow the Definition of Done above.
Do not fabricate approvals and maintain monorepo governance rules.
```
