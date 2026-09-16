# Comando /factory

Gera código de aplicação e integrações para stacks multi-serviço através da pipeline Factory.

## Uso:
`/factory --plano <caminho_do_plano> --pasta <pasta_destino> [argumentos...]`

## Ação:
Executa a skill `skills/aidd-factory-runner` para orquestrar as fases determinísticas e geradores de código da aplicação.
Equivalente CLI: `python ecossistema.py factory <args>`
