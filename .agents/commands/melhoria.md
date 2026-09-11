# Comando /melhoria

Recebe um pedido de melhoria em linguagem natural, investiga o codigo real de forma profunda e gera um relatorio com nota (0-10) em `docs/melhorias/` — etapa anterior ao `/plan`.

## Uso:
`/melhoria <descricao em linguagem natural do que quer melhorar>`

## Acao:
Executa a skill `melhoria` para investigar o codigo (preferencialmente via `code-review-graph`, com fallback universal para Grep/Glob/Read), atribuir uma Nota Atual (0-10) sempre com evidencia real, e gerar o par `.html`+`.json` do relatorio. Ao final, sugere iniciar o `/plan` a partir do relatorio — nunca dispara sozinho.

Equivalente CLI: `python ecossistema.py melhoria init --pedido "<texto>" [--nome ...] [--nota-atual ...] [--evidencia ...] [--resumo ...] [--achados ...] [--riscos ...] [--recomendacao ...]`
