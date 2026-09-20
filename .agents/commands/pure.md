---
description: Dispara o Fluxo 01 (Do Zero Puro) da Tríade Canônica
argument-hint: "<nome_do_projeto> [dominio]"
---

# Comando /pure

Dispara o Fluxo 01 (`aidd-pure`) da Tríade Canônica: geração de software de ponta a ponta do zero absoluto via TDD e Monólito Modular VSA.

## Uso:
`/pure <nome_do_projeto> [dominio]`

## Ação:
Executa a skill `aidd-pure` (ou `fluxo-01-runner`), que coleta os parâmetros e dispara deterministicamente o comando CLI:
`python ecossistema.py pure --nome "<nome>" --slug <slug> --dominio <dominio> --pasta ./projetos/<slug>`
(ou `python ecossistema.py run-fluxo --fluxo pure ...`)
