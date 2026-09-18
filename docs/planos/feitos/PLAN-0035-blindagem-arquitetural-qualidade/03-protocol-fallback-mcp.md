# Item 3 — protocol-fallback-mcp

> **Escopo:** Implementar o Quality Gate G_PROTOCOL_FALLBACK.py para garantir paridade 1:1 e fallback total entre MCP Tools e rotas REST documentadas no Swagger/OpenAPI.
> **Status:** [EM EXECUCAO]
> **Nota Atual (0-10):** 9.6 — evidencia: Relatorio de Atualidade e Protocolos de IA
> **Nota Alvo (0-10):** 10.0
> **Nota Real (pos-implementacao):** [Pendente - preencher somente apos o fechamento real deste item/iniciativa, via o mesmo mecanismo que mediu a Nota Atual]

---

## Contexto ja investigado

- O ecossistema gera nativamente `/docs` (OpenAPI) e `/mcp` (MCP Server) no mesmo `server.py`.
- O risco levantado na auditoria foi a dependencia excessiva de um protocolo jovem (MCP).
- O fallback canônico e garantir que 100% das tools expostas no MCP possuam rota REST correspondente no Swagger, permitindo operacao mesmo se o MCP falhar.

## Definicao de Pronto

1. Implementar `gates/G_PROTOCOL_FALLBACK.py` que analisa contratos de projetos/templates (`quarteto_sine_qua_non/swagger_spec.json` vs `mcp_studio.json` ou endpoints do `server.py`).
2. Implementar `gates/test_g_protocol_fallback.py` com testes reais cobrindo paridade e rejeicao de tools MCP orfas.
3. Integrar ao `ecossistema.py audit` e validar exit 0.
4. Modo /goal ativo: [executar o fluxo alvo do inicio ao fim corrigindo TODOS os bugs, erros, inconsistencias, backlogs encontrados durante a execucao da implementacao (Encontrou? Corrige!) | IMPLEMENTACAO 100% sem erros, bugs, backlogs, ou debitos tecnicos].

## Criterio de saida

- Arquivos `gates/G_PROTOCOL_FALLBACK.py` e `gates/test_g_protocol_fallback.py` criados e testados.
- Testes reais passando com exit 0 sem stubs.
- Verificacao de fallback aprovada no ecossistema.

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Operando em modo /goal com:
[ Objetivo: executar o fluxo alvo do inicio ao fim corrigindo TODOS os bugs, erros, inconsistencias, backlogs encontrados durante a execucao da implementacao (Encontrou? Corrige!) | Condicao: IMPLEMENTACAO 100% sem erros, bugs, backlogs, ou debitos tecnicos ]

Implemente o Item 3: protocol-fallback-mcp.
Crie gates/G_PROTOCOL_FALLBACK.py e gates/test_g_protocol_fallback.py.
Assegure que toda tool MCP possua contrapartida REST funcional documentada no Swagger.
Integre ao ecossistema.py e garanta 100% dos testes passando com exit 0.
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
Operating in /goal mode with:
[ Objective: execute target flow end-to-end fixing ALL bugs, errors, inconsistencies, and backlogs encountered during implementation (Found it? Fix it!) | Condition: 100% IMPLEMENTATION with zero errors, bugs, backlogs, or technical debt ]

Implement Item 3: protocol-fallback-mcp.
Create gates/G_PROTOCOL_FALLBACK.py and gates/test_g_protocol_fallback.py.
Ensure every MCP tool has a corresponding functional REST counterpart documented in Swagger.
Integrate into ecossistema.py and ensure 100% tests passing with exit 0.
```
