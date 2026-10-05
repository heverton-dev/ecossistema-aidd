# AGENTS.md — Fase 00: Bootstrap

## Objetivo

Diagnosticar o ambiente antes de qualquer outra fase rodar: hardware do
host (SO, CPU, disco disponível) e estado do repositório git (branch,
working tree limpo, remoto configurado). Esta fase é **mecânica
determinística** — nenhuma chamada de LLM é necessária aqui.

## Escopo Permitido

- Ler informações de SO, hardware e `git status` / `git rev-parse`.
- Escrever um relatório de diagnóstico em `report.json` dentro desta pasta.
- Bloquear o pipeline (`exit != 0`) se o repositório não for git ou se o
  working tree tiver conflitos não resolvidos.

## Escopo Proibido

- Não editar código de produção.
- Não avançar para `phase_01_requirements` sem o diagnóstico completo.
- Não usar nenhum MCP: esta fase não invoca cognição de IA.

## Gate de Saída

`exit 0` somente se: SO suportado (windows/darwin/linux), git presente,
working tree sem conflitos ativos.
