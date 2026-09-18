# Item 1 — isolamento-ast-fatias

> **Escopo:** Criar o Quality Gate G_ISOLATION_AUDIT.py e sua suite de testes test_g_isolation_audit.py para analise estatica por AST impedindo imports cruzados diretos entre fatias VSA (src/features/*).
> **Status:** [EM EXECUCAO]
> **Nota Atual (0-10):** 9.1 — evidencia: Auditoria Profunda VSA
> **Nota Alvo (0-10):** 10.0
> **Nota Real (pos-implementacao):** [Pendente - preencher somente apos o fechamento real deste item/iniciativa, via o mesmo mecanismo que mediu a Nota Atual]

---

## Contexto ja investigado

- O Monolito Modular VSA exige que fatias verticais em `src/features/` sejam mutuamente isoladas.
- Uma fatia nunca deve importar de outra fatia (`from src.features.outra import ...`); a comunicacao deve ocorrer via `src/core/events.py` ou interfaces em `src/core/`.
- Falta um gate deterministico que garanta isso matematicamente via AST.

## Definicao de Pronto

1. Implementar `gates/G_ISOLATION_AUDIT.py` com `ast.parse` que varre `src/features/` em projetos e templates, detectando violacoes de import cruzado.
2. Implementar `gates/test_g_isolation_audit.py` com testes unitarios cobrindo cenarios validos e casos de violacao com exit 1.
3. Integrar `G_ISOLATION_AUDIT` a lista de gates em `ecossistema.py` e verificar aprovacao em `python ecossistema.py audit`.
4. Modo /goal ativo: [executar o fluxo alvo do inicio ao fim corrigindo TODOS os bugs, erros, inconsistencias, backlogs encontrados durante a execucao da implementacao (Encontrou? Corrige!) | IMPLEMENTACAO 100% sem erros, bugs, backlogs, ou debitos tecnicos].

## Criterio de saida

- Arquivos criados e testados: `gates/G_ISOLATION_AUDIT.py` e `gates/test_g_isolation_audit.py`.
- Testes reais passando com exit 0 sem stubs.
- `python ecossistema.py audit` executando o novo gate e retornando sucesso.

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Operando em modo /goal com:
[ Objetivo: executar o fluxo alvo do inicio ao fim corrigindo TODOS os bugs, erros, inconsistencias, backlogs encontrados durante a execucao da implementacao (Encontrou? Corrige!) | Condicao: IMPLEMENTACAO 100% sem erros, bugs, backlogs, ou debitos tecnicos ]

Implemente o Item 1: isolamento-ast-fatias.
Crie gates/G_ISOLATION_AUDIT.py e gates/test_g_isolation_audit.py.
Valide imports AST cruzados entre fatias VSA (src/features/*).
Integre ao ecossistema.py e garanta 100% de testes passando com exit 0.
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
Operating in /goal mode with:
[ Objective: execute target flow end-to-end fixing ALL bugs, errors, inconsistencies, and backlogs encountered during implementation (Found it? Fix it!) | Condition: 100% IMPLEMENTATION with zero errors, bugs, backlogs, or technical debt ]

Implement Item 1: isolamento-ast-fatias.
Create gates/G_ISOLATION_AUDIT.py and gates/test_g_isolation_audit.py.
Validate AST cross-slice imports in VSA (src/features/*).
Integrate into ecossistema.py and ensure 100% tests passing with exit 0.
```
