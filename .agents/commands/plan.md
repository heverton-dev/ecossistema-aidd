# Comando /plan

Gera a estrutura padrao e rascunhos de planos de auditoria, evolucao ou testes em `docs/planos/`.

## Uso:
`/plan <nome-da-iniciativa> [--itens "Item 1" "Item 2"]`

## Acao:
Executa a skill `planos-auditoria-runner` para confirmar escopo com o usuario humano, gerar o esqueleto estrutural (`00-PROCESSO-E-DECISOES.md` e `NN-<item>.md`) e checar cercas de codigo sem fabricar decisoes ou aprovacoes.

Equivalente CLI: `python ecossistema.py plan init <nome-da-iniciativa> [--itens "Item 1" "Item 2"]`
Verificacao de cercas: `python ecossistema.py plan check-fences <caminho-ou-pasta>`