# Comando /enterprise

Injeta componentes de missão crítica com validação de hashes SHA-256 e conformidade Zero-Trust no `aidd-enterprise`.

## Uso:
`/enterprise <tipo> <nome>`

## Ação:
Executa a skill `skills/aidd-enterprise-runner`. Tipos suportados: `skill`, `rule`, `mcp`, `spec`, `config`, `hook`, `agent`.
Equivalente CLI: `python ecossistema.py enterprise inject <tipo> <nome>`
