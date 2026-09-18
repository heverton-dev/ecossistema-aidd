# Item 5 — governanca-rotas-carta

> **Escopo:** Harmonizar rotas do Quarteto Sine Qua Non no AGENTS.md (Lei #10: /docs e /docs/guia), atualizar Enciclopedia Canônica e rodar auditoria geral.
> **Status:** [EM EXECUCAO]
> **Nota Atual (0-10):** 9.4 — evidencia: Auditoria de rotas e Carta Magna
> **Nota Alvo (0-10):** 10.0
> **Nota Real (pos-implementacao):** [Pendente - preencher somente apos o fechamento real deste item/iniciativa, via o mesmo mecanismo que mediu a Nota Atual]

---

## Contexto ja investigado

- A Lei #10 no `AGENTS.md` ainda continha referencia defasada a `/swagger` e `/docs` em vez de `/docs` (Swagger) e `/docs/guia` (Guia do Utilizador).
- A documentacao `docs/explicacoes/16-09-2026_CONSOLIDACAO-DECISOES-ARQUITETURA-ECOSSISTEMA.md` precisa registrar os novos Quality Gates criados nesta iniciativa.
- A auditoria completa `python ecossistema.py audit` deve rodar com 100% dos gates verdes (Exit Code 0).

## Definicao de Pronto

1. Corrigir no `AGENTS.md` a redacao da Lei #10 refletindo `/docs` para Swagger Studio e `/docs/guia` para Guia do Utilizador.
2. Atualizar a Enciclopedia Canonica registrando os Quality Gates `G_ISOLATION_AUDIT`, `G_PROTOCOL_FALLBACK`, `G_LLM_PROMPT_SHIELD` e a especificacao Light-Lane.
3. Executar `python ecossistema.py audit` e atestar 100% de sucesso sem pendencias.
4. Modo /goal ativo: [executar o fluxo alvo do inicio ao fim corrigindo TODOS os bugs, erros, inconsistencias, backlogs encontrados durante a execucao da implementacao (Encontrou? Corrige!) | IMPLEMENTACAO 100% sem erros, bugs, backlogs, ou debitos tecnicos].

## Criterio de saida

- `AGENTS.md` e Enciclopedia Canônica sincronizados.
- `python ecossistema.py audit` retornando exit 0 com todos os gates passando.
- Relatorio final e encerramento do plano com nota 10.0.

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Operando em modo /goal com:
[ Objetivo: executar o fluxo alvo do inicio ao fim corrigindo TODOS os bugs, erros, inconsistencias, backlogs encontrados durante a execucao da implementacao (Encontrou? Corrige!) | Condicao: IMPLEMENTACAO 100% sem erros, bugs, backlogs, ou debitos tecnicos ]

Implemente o Item 5: governanca-rotas-carta.
Harmonize a Lei #10 no AGENTS.md e atualize a Enciclopedia Canonica.
Rode a auditoria geral e garanta exit 0 absoluto em todos os gates.
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
Operating in /goal mode with:
[ Objective: execute target flow end-to-end fixing ALL bugs, errors, inconsistencies, and backlogs encountered during implementation (Found it? Fix it!) | Condition: 100% IMPLEMENTATION with zero errors, bugs, backlogs, or technical debt ]

Implement Item 5: governanca-rotas-carta.
Harmonize Law #10 in AGENTS.md and update Canonical Encyclopedia.
Run global audit and ensure absolute exit 0 on all quality gates.
```
