# Item 2 — light-lane-consultas

> **Escopo:** Padronizar e documentar a convencao VSA Light-Lane (Query Slices) para operacoes read-only diretas com DTOs sem boilerplate de Railway Monad.
> **Status:** [EM EXECUCAO]
> **Nota Atual (0-10):** 9.1 — evidencia: Analise arquitetural de boilerplate VSA
> **Nota Alvo (0-10):** 10.0
> **Nota Real (pos-implementacao):** [Pendente - preencher somente apos o fechamento real deste item/iniciativa, via o mesmo mecanismo que mediu a Nota Atual]

---

## Contexto ja investigado

- VSA completo e Railway Oriented Programming (`Result[Ok, Err]`) sao essenciais para mutacoes e comandos de negocio com regras e side-effects.
- Para consultas puras (read-only queries, listas, lookups), o overhead de criar command handlers e wrapping em Result monad aumenta desnecessariamente os tokens e arquivos.
- A solucao e a formalizacao da via rapida (Light-Lane) de leitura direta via DTOs/Query Handlers.

## Definicao de Pronto

1. Criar documentacao de padrao arquitetural `docs/padroes/PADRAO-VSA-LIGHT-LANE.md` detalhando a fronteira entre Command Slices (Railway estrito) e Query Slices (Light-Lane).
2. Fornecer template representativo em `tools/aidd-master/templates/v2/src/core/cqrs.py` suportando execucao leve de queries.
3. Testar via pytest deterministico comprovando funcionamento das queries sem quebra de contratos.
4. Modo /goal ativo: [executar o fluxo alvo do inicio ao fim corrigindo TODOS os bugs, erros, inconsistencias, backlogs encontrados durante a execucao da implementacao (Encontrou? Corrige!) | IMPLEMENTACAO 100% sem erros, bugs, backlogs, ou debitos tecnicos].

## Criterio de saida

- Documento `docs/padroes/PADRAO-VSA-LIGHT-LANE.md` criado e validado.
- Testes reais passando com exit 0 sem stubs.
- Quality Gates de arquitetura mantidos em conformidade.

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Operando em modo /goal com:
[ Objetivo: executar o fluxo alvo do inicio ao fim corrigindo TODOS os bugs, erros, inconsistencias, backlogs encontrados durante a execucao da implementacao (Encontrou? Corrige!) | Condicao: IMPLEMENTACAO 100% sem erros, bugs, backlogs, ou debitos tecnicos ]

Implemente o Item 2: light-lane-consultas.
Crie docs/padroes/PADRAO-VSA-LIGHT-LANE.md e atualize os templates/exemplos para suportar Query Slices diretas com DTOs.
Garanta integridade arquitetural e 100% dos testes passando.
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
Operating in /goal mode with:
[ Objective: execute target flow end-to-end fixing ALL bugs, errors, inconsistencies, and backlogs encountered during implementation (Found it? Fix it!) | Condition: 100% IMPLEMENTATION with zero errors, bugs, backlogs, or technical debt ]

Implement Item 2: light-lane-consultas.
Create docs/padroes/PADRAO-VSA-LIGHT-LANE.md and update templates/examples to support direct Query Slices with DTOs.
Ensure architectural integrity and 100% tests passing.
```
