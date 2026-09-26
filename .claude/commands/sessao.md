---
description: Registra o ID e os metadados da sessao atual em secoes/
argument-hint: "[id-da-sessao]"
---

# Comando /sessao

Registra o ID da sessao agentica atual, o harness, o modelo e o titulo em `secoes/historico_sessoes.json` e `secoes/INDICE-SESSOES.md`.

## Uso:
`/sessao [id-da-sessao]` (tambem `/session` e `/id`)

## Acao:
Executa a skill `aidd-session`, que roda:
`python ecossistema.py sessao registrar --id "<ID>" --harness "<HARNESS>" --modelo "<MODELO>" --titulo "<TITULO>"`
