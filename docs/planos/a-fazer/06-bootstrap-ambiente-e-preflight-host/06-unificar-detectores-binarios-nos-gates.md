# Item — unificar-detectores-binarios-nos-gates

> **Escopo:** Refatorar G_HADOLINT, G_INFRA_COMPOSE e G_ECOSSISTEMA_INTEGRIDADE para consumirem os detectores centralizados de preflight_host, eliminando código duplicado de shutil.which.
> **Status:** [RASCUNHO — Aguardando Aprovação Humana]

---

## Contexto já investigado

- Existem 4 implementações distintas de busca de binários nos gates com lógicas dispersas de fallback [BP-3].

## Definição de Pronto

1. Extrair detectores de binários para `gates/utils_preflight.py` ou `scripts/preflight_host.py`.
2. Atualizar G_HADOLINT e G_INFRA_COMPOSE para importar a rotina única.
3. Padronizar a mensagem de falha em caso de ausência do binário, indicando `preflight-host --fix`.

## Critério de saída

- Zero duplicação de rotinas shutil.which nos gates.
- Testes reais passando sem stubs falsos.
- Gates de integridade aprovados.

## Prompt de Execução (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Você vai implementar o Item: unificar-detectores-binarios-nos-gates.
Siga rigorosamente a Definição de Pronto acima:
1. Extrair detectores de binários para `gates/utils_preflight.py` ou `scripts/preflight_host.py`.
2. Atualizar G_HADOLINT e G_INFRA_COMPOSE para importar a rotina única.
3. Padronizar a mensagem de falha em caso de ausência do binário, indicando `preflight-host --fix`.
Garanta exit 0 nos testes e gates pertinentes.
```

## Prompt de Execução — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item: unificar-detectores-binarios-nos-gates.
Strictly follow the Definition of Done above:
1. Extrair detectores de binários para `gates/utils_preflight.py` ou `scripts/preflight_host.py`.
2. Atualizar G_HADOLINT e G_INFRA_COMPOSE para importar a rotina única.
3. Padronizar a mensagem de falha em caso de ausência do binário, indicando `preflight-host --fix`.
Ensure exit code 0 across relevant tests and gates.
```
