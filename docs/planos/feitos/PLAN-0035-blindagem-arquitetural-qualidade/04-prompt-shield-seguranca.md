# Item 4 — prompt-shield-seguranca

> **Escopo:** Implementar Quality Gate G_LLM_PROMPT_SHIELD.py e modulo deterministico de sanitizacao de prompt injection em src/core/security.py.
> **Status:** [EM EXECUCAO]
> **Nota Atual (0-10):** 9.6 — evidencia: OWASP GenAI Top 10 e Relatorio de Auditoria
> **Nota Alvo (0-10):** 10.0
> **Nota Real (pos-implementacao):** [Pendente - preencher somente apos o fechamento real deste item/iniciativa, via o mesmo mecanismo que mediu a Nota Atual]

---

## Contexto ja investigado

- Agentes recebem entradas textuais em ferramentas MCP e APIs de integracao.
- O auditor externo apontou risco de Prompt Injection e agência descontrolada (OWASP LLM01).
- Solucao alinhada a Lei #1 (Determinismo Primeiro): modulo deterministico de sanitizacao textual em `src/core/security.py` (bloqueio de tags de sistema, escape de delimitadores e deteccao de padroes de fuga conhecidos).

## Definicao de Pronto

1. Implementar funcao deterministica `sanitize_llm_input(text: str) -> SanitizedResult` em `templates/v2/security.py` / `src/core/security.py`.
2. Implementar `gates/G_LLM_PROMPT_SHIELD.py` e `gates/test_g_llm_prompt_shield.py` testando ataques adversariais tipicos de prompt injection.
3. Integrar ao `ecossistema.py audit` com exit 0.
4. Modo /goal ativo: [executar o fluxo alvo do inicio ao fim corrigindo TODOS os bugs, erros, inconsistencias, backlogs encontrados durante a execucao da implementacao (Encontrou? Corrige!) | IMPLEMENTACAO 100% sem erros, bugs, backlogs, ou debitos tecnicos].

## Criterio de saida

- Arquivos `gates/G_LLM_PROMPT_SHIELD.py` e testes criados.
- Modulo de sanitizacao funcional e deterministico sem chamadas a LLM externa.
- Quality Gates aprovados com exit 0.

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Operando em modo /goal com:
[ Objetivo: executar o fluxo alvo do inicio ao fim corrigindo TODOS os bugs, erros, inconsistencias, backlogs encontrados durante a execucao da implementacao (Encontrou? Corrige!) | Condicao: IMPLEMENTACAO 100% sem erros, bugs, backlogs, ou debitos tecnicos ]

Implemente o Item 4: prompt-shield-seguranca.
Crie gates/G_LLM_PROMPT_SHIELD.py e gates/test_g_llm_prompt_shield.py.
Adicione sanitizacao deterministica anti-injection em security.py.
Integre ao ecossistema.py e garanta 100% dos testes passando com exit 0.
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
Operating in /goal mode with:
[ Objective: execute target flow end-to-end fixing ALL bugs, errors, inconsistencies, and backlogs encountered during implementation (Found it? Fix it!) | Condition: 100% IMPLEMENTATION with zero errors, bugs, backlogs, or technical debt ]

Implement Item 4: prompt-shield-seguranca.
Create gates/G_LLM_PROMPT_SHIELD.py and gates/test_g_llm_prompt_shield.py.
Add deterministic anti-injection sanitization in security.py.
Integrate into ecossistema.py and ensure 100% tests passing with exit 0.
```
