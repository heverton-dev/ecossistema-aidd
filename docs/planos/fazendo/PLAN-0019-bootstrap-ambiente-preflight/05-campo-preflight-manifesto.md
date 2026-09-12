# Item — campo-preflight-manifesto-dependencias-externas

> **Escopo:** Expandir o manifesto `gates/dependencias_externas.json` com o campo `preflight` declarando binários de sistema e versões mínimas exigidas por cada skill ou MCP.
> **Status:** [EM EXECUCAO]
> **Auditoria por reproducao real (11-09-2026):** NAO-FEITO. dependencias_externas.json nao tem a chave preflight.

---

## Contexto já investigado

- O manifesto declarava apenas comandos de instalação e verificação de arquivos, sem explicitar os pré-requisitos de runtime de sistema.

## Definição de Pronto

1. Adicionar chave `preflight: {binario, versao_minima}` para cada skill/MCP que depende de ferramentas externas (ex: npx para impeccable, docker para cofre).
2. Integrar a checagem no `python ecossistema.py dependencia verify`.
3. Bloquear status como AUSENTE se o binário de sistema associado não estiver presente.

## Critério de saída

- Manifesto único agora governa tanto artefatos quanto pré-requisitos de sistema.
- Testes reais passando sem stubs falsos.
- Gates de integridade aprovados.

## Prompt de Execução (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Você vai implementar o Item: campo-preflight-manifesto-dependencias-externas.
Siga rigorosamente a Definição de Pronto acima:
1. Adicionar chave `preflight: {binario, versao_minima}` para cada skill/MCP que depende de ferramentas externas (ex: npx para impeccable, docker para cofre).
2. Integrar a checagem no `python ecossistema.py dependencia verify`.
3. Bloquear status como AUSENTE se o binário de sistema associado não estiver presente.
Garanta exit 0 nos testes e gates pertinentes.
```

## Prompt de Execução — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item: campo-preflight-manifesto-dependencias-externas.
Strictly follow the Definition of Done above:
1. Adicionar chave `preflight: {binario, versao_minima}` para cada skill/MCP que depende de ferramentas externas (ex: npx para impeccable, docker para cofre).
2. Integrar a checagem no `python ecossistema.py dependencia verify`.
3. Bloquear status como AUSENTE se o binário de sistema associado não estiver presente.
Ensure exit code 0 across relevant tests and gates.
```
