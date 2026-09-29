# Comando /evolucao (Pipeline de Evolução Técnica)

> **Pipeline de Evolução Técnica:** Executa os tickets do plano de evolução em worktrees efêmeras do Git, com quality gates por fase e barreira de join controlada.

Dispara a execução do pipeline de evolução técnica a partir do `PLANO-EVOLUCAO.json` (ou compila automaticamente do `PLANO-EVOLUCAO.md`).

## Uso:
`/evolucao [ferramenta_ou_caminho_manifesto]`

## Ação:
Executa a skill `aidd-evolution`: isola cada ticket em worktree Git efêmera, aciona o agente configurado com Watchdog termodinâmico, valida os quality gates da fase e só faz o merge no branch principal após aprovação dos gates finais e confirmação humana.

Equivalente CLI: `python ecossistema.py evolucao [ferramenta]` ou `python ecossistema.py evolucao --manifest <caminho.json>`
Para aprovar o merge após os testes: `python ecossistema.py evolucao --manifest <caminho.json> --aprovar`
