# Item 1 — fechar-nucleo-compartilhado-e-honestidade-rotulos

> **Escopo:** Extração física da fonte única `componentes/compartilhado/src-core/` para os 27 arquivos duplicados entre `aidd-master` e `aidd-enterprise`, resolução das 3 divergências silenciosas documentadas e alinhamento de honestidade de rótulos nos gates.
> **Status:** [RASCUNHO — Aguardando Aprovação Humana]

---

## Contexto já investigado

- 27 arquivos byte-idênticos (8.781 linhas) compartilhados entre `tools/aidd-master/src/core` e `tools/aidd-enterprise/src/core`.
- 3 divergências silenciosas identificadas:
  1. `mcp_server.py`: `register_injected_tools` existe no master mas não no enterprise.
  2. `intent_router.py`: gancho vs hook.
  3. `materializador.py`: formato de hook bash vs JSON.
- Gates `G_SEGURANCA`, `G_ARQUITETURA` e `G_PERFORMANCE` em master/enterprise usam termos como "blindagem militar" reprovados por `G_HONESTIDADE_ROTULO`.

## Definição de Pronto

1. Criar pasta canônica `componentes/compartilhado/src-core/` como fonte única.
2. Adicionar sincronização mecânica determinística para `tools/aidd-master/src/core` e `tools/aidd-enterprise/src/core`.
3. Resolver as 3 divergências adotando o formato JSON para hooks e garantindo `register_injected_tools` no enterprise.
4. Ajustar mensagens de prints/logs em `scripts/gates/G_SEGURANCA.py`, `G_ARQUITETURA.py` e `G_PERFORMANCE.py` para termos técnicos auditáveis.
5. Rodar `python gates/G_DRIFT_NUCLEO_COMPARTILHADO.py` e comprovar exit 0.
6. Rodar `python gates/G_HONESTIDADE_ROTULO.py` e comprovar exit 0.

## Critério de saída

- Zero divergência não documentada entre master e enterprise.
- Gates `G_DRIFT_NUCLEO_COMPARTILHADO` e `G_HONESTIDADE_ROTULO` aprovados com exit 0.
- Testes unitários de master e enterprise passando 100%.

## Prompt de Execução (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Você vai implementar o Item 1 do plano de Reestruturação DDD/Clean Architecture: fechar-nucleo-compartilhado-e-honestidade-rotulos.

Siga estritamente a Definição de Pronto:
1. Crie a fonte única em `componentes/compartilhado/src-core/` para os 27 arquivos de núcleo compartilhado entre master e enterprise.
2. Resolva as 3 divergências silenciosas (unificar hooks em JSON, alinhar register_injected_tools no mcp_server do enterprise).
3. Sincronize deterministicamente para `tools/aidd-master/src/core/` e `tools/aidd-enterprise/src/core/`.
4. Corrija os termos de marketing nos prints dos gates para nomes técnicos objetivos, garantindo aprovação no G_HONESTIDADE_ROTULO.
5. Execute os gates:
   - python gates/G_DRIFT_NUCLEO_COMPARTILHADO.py
   - python gates/G_HONESTIDADE_ROTULO.py
   - pytest tools/aidd-master/tests tools/aidd-enterprise/tests
Garanta exit 0 em todos.
```

## Prompt de Execução — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 1 of the DDD/Clean Architecture Restructuring plan: fechar-nucleo-compartilhado-e-honestidade-rotulos.

Strictly follow the Definition of Done:
1. Establish the single source of truth in `componentes/compartilhado/src-core/` for the 27 duplicated core files between master and enterprise.
2. Resolve the 3 silent divergences (unify hook formats to JSON, port register_injected_tools to enterprise's mcp_server).
3. Synchronize mechanically to `tools/aidd-master/src/core/` and `tools/aidd-enterprise/src/core/`.
4. Remove unverified marketing terms ("blindagem militar") from security gates to satisfy G_HONESTIDADE_ROTULO.
5. Run and verify:
   - python gates/G_DRIFT_NUCLEO_COMPARTILHADO.py
   - python gates/G_HONESTIDADE_ROTULO.py
   - pytest tools/aidd-master/tests tools/aidd-enterprise/tests
Ensure exit code 0 across all verifications.
```
