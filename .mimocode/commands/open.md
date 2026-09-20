---
description: Dispara o Fluxo 02 (Motores Open-Source) da Tríade Canônica
argument-hint: "<nome_do_projeto> [dominio]"
---

# Comando /open

Dispara o Fluxo 02 (`aidd-open`) da Tríade Canônica: criação acelerada integrando motores open-source robustos em fatias verticais VSA.

## Uso:
`/open <nome_do_projeto> [dominio]`

## Ação:
Executa a skill `aidd-open` (ou `fluxo-02-runner`), que coleta os parâmetros e dispara deterministicamente o comando CLI:
`python ecossistema.py open --nome "<nome>" --slug <slug> --dominio <dominio> --pasta ./projetos/<slug>`
(ou `python ecossistema.py run-fluxo --fluxo open ...`)
