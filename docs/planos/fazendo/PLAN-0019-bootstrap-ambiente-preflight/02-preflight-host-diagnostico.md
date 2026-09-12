# Item — preflight-host-diagnostico-binarios-sistema

> **Escopo:** Criar o comando determinístico `python ecossistema.py preflight-host [--json] [--fix]` para diagnóstico instantâneo (< 2s) de binários do sistema (Git, Node, Docker, Hadolint, Checkov).
> **Status:** [EM EXECUCAO]
> **Auditoria por reproducao real (11-09-2026):** NAO-FEITO. scripts/preflight_host.py nao existe e nao ha subcomando preflight-host.

---

## Contexto já investigado

- Atualmente cada comando descobre a ausência de binários de forma tardia e desconexa [BP-2, BP-3, BP-5], sem diagnóstico unificado de pré-requisitos do host.

## Definição de Pronto

1. Criar módulo `scripts/preflight_host.py` com rotinas únicas de detecção por binário (caminho, versão encontrada, versão mínima requerida).
2. Adicionar subcomando `preflight-host` no `ecossistema.py` com saída em tabela e flag `--json`.
3. Reutilizar detectores existentes de Hadolint e Checkov como fonte única de verdade.
4. Validar tempo de execução < 2 segundos sem dependência de rede.

## Critério de saída

- Comando preflight-host funcional com diagnóstico completo e saída estruturada.
- Testes reais passando sem stubs falsos.
- Gates de integridade aprovados.

## Prompt de Execução (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Você vai implementar o Item: preflight-host-diagnostico-binarios-sistema.
Siga rigorosamente a Definição de Pronto acima:
1. Criar módulo `scripts/preflight_host.py` com rotinas únicas de detecção por binário (caminho, versão encontrada, versão mínima requerida).
2. Adicionar subcomando `preflight-host` no `ecossistema.py` com saída em tabela e flag `--json`.
3. Reutilizar detectores existentes de Hadolint e Checkov como fonte única de verdade.
4. Validar tempo de execução < 2 segundos sem dependência de rede.
Garanta exit 0 nos testes e gates pertinentes.
```

## Prompt de Execução — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item: preflight-host-diagnostico-binarios-sistema.
Strictly follow the Definition of Done above:
1. Criar módulo `scripts/preflight_host.py` com rotinas únicas de detecção por binário (caminho, versão encontrada, versão mínima requerida).
2. Adicionar subcomando `preflight-host` no `ecossistema.py` com saída em tabela e flag `--json`.
3. Reutilizar detectores existentes de Hadolint e Checkov como fonte única de verdade.
4. Validar tempo de execução < 2 segundos sem dependência de rede.
Ensure exit code 0 across relevant tests and gates.
```
