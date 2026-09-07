# Comando /dependencia

Instala e registra skills e MCPs de terceiros usados pelo próprio agente de IA neste monorepo (não é para MCPs de produtos gerados — esses seguem `componentes/<escopo>/mcps/`).

## Uso:
`/dependencia bootstrap` — instala/registra tudo que já está declarado (rodar 1x após clone)
`/dependencia skill <nome ou pedido>` — adiciona uma nova skill externa
`/dependencia mcp <nome ou pedido>` — registra um novo MCP de terceiros

## Ação:
Executa a skill `skills/dependencia-runner`, que completa os dados que faltarem (pacote, comando de instalação, nomes de variável de ambiente) e delega para `python ecossistema.py dependencia <acao> ...`.
