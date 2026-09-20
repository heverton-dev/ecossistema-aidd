---
description: Comanda a ferramenta individual aidd-bridge para acoes atomicas
argument-hint: "[scan|convert-db|merge|pack] <args>"
---

# Comando /bridge

Comanda a ferramenta individual `aidd-bridge` para ingestão, conversão de banco e empacotamento de aplicações low-code (Lovable, v0, Bolt).

## Uso:
- `/bridge scan <caminho>`
- `/bridge convert-db <caminho>`
- `/bridge merge <app1> <app2> --output <destino>`
- `/bridge pack <caminho> [--domain meusite.com]`

## Ação:
Executa a skill `skills/aidd-bridge-runner` para acionar as operações atômicas da engine `tools/aidd-bridge`.
Equivalente CLI: `python ecossistema.py bridge [scan|convert-db|merge|pack] <args>`