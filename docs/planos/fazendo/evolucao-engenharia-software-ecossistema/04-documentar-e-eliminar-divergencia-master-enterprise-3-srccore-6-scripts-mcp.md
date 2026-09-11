# Item 4 — Documentar e eliminar divergencia master-enterprise (3 src/core + 6 scripts + mcp/)

> **Escopo:** Resolver a divergencia ja mapeada entre `aidd-master` e `aidd-enterprise` em: 3 arquivos de `src/core` (detector_camada.py, profiles_registry.py, schema_injector_request.json), 6 arquivos de `scripts` (aidd.py, compose_suite.py, G_INJECT.py, openapi_to_ts.py, provision_project.py, run_all.py), a pasta `mcp/` (so existe no master) e a pasta `injector/` (so existe no enterprise). Por item: ou os dois lados convergem pro mesmo conteudo, ou a diferenca e documentada como intencional.
> **Status:** [EM EXECUCAO]
> **Nota Atual (0-10):** 5.0 — evidencia: diff master vs enterprise: src/core diverge detector_camada.py, profiles_registry.py, schema_injector_request.json; mcp/ so no master; scripts divergem aidd.py, compose_suite.py, G_INJECT.py, openapi_to_ts.py, provision_project.py, run_all.py; injector/ so no enterprise
> **Nota Alvo (0-10):** 9.0
> **Nota Real (pos-implementacao):** [Pendente - preencher somente apos o fechamento real deste item/iniciativa, via o mesmo mecanismo que mediu a Nota Atual]

---

## Contexto ja investigado

- Diff real master vs enterprise ja rodado: divergencias confirmadas em src/core (detector_camada.py, profiles_registry.py, schema_injector_request.json), em scripts (aidd.py, compose_suite.py, G_INJECT.py, openapi_to_ts.py, provision_project.py, run_all.py), e nas pastas mcp/ (so master) e injector/ (so enterprise).

## Definicao de Pronto

1. Cada uma das 3 divergencias em src/core foi resolvida (convergida) ou documentada como intencional, com justificativa.
2. Cada uma das 6 divergencias em scripts foi resolvida ou documentada como intencional.
3. mcp/ (so master) e injector/ (so enterprise) foram documentados explicitamente como exclusivos de cada lado (ou unificados, se fizer sentido tecnico).
4. Documento de decisao registrado (ex.: secao em AGENTS.md ou arquivo proprio) explicando o resultado de cada divergencia.

## Criterio de saida

- Novo diff master vs enterprise rodado de verdade confirma que so restam divergencias documentadas como intencionais.
- Testes de master e enterprise continuam passando com exit 0.

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai implementar o Item 4: Documentar e eliminar divergencia master-enterprise (3 src/core + 6 scripts + mcp/).
Siga rigorosamente a Definicao de Pronto acima.
Nao invente aprovacoes e mantenha as regras do monorepo.
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 4: Documentar e eliminar divergencia master-enterprise (3 src/core + 6 scripts + mcp/).
Strictly follow the Definition of Done above.
Do not fabricate approvals and maintain monorepo governance rules.
```
