---
description: Nome antigo do motor do Fluxo 03 (use /freedom ou freedom-motor)
argument-hint: "[scan|convert-db|merge|pack] <args>"
---

# Comando /bridge (nome antigo)

Apelido de 1 ciclo para as operações atômicas do motor do Fluxo 03 (`modulos/02-triade-motores/fluxo-03-freedom/core/aidd-freedom`): ingestão, conversão de banco e empacotamento de aplicações low-code (Lovable, v0, Bolt).

## Uso:
- `/bridge scan <caminho>`
- `/bridge convert-db <caminho>`
- `/bridge merge <app1> <app2> --output <destino>`
- `/bridge pack <caminho> [--domain meusite.com]`

## Ação:
Executa a skill `aidd-freedom`, seção "Engine only".
Equivalente CLI: `python ecossistema.py freedom-motor [scan|convert-db|merge|pack] <args>` (o antigo `python ecossistema.py bridge ...` ainda funciona e avisa "nome antigo").
