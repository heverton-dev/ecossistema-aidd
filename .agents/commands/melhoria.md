# Comando /melhoria (etapa 1 de 3)

> **Fluxo unico (3 etapas, cada uma para pra decisao do usuario):** `/melhoria` -> `/plan` -> `/orchestrate`. Nenhuma dispara a seguinte sozinha.

Recebe um pedido de melhoria em linguagem natural, investiga o codigo real de forma profunda e gera um relatorio com nota (0-10) em `docs/melhorias/` — etapa anterior ao `/plan`.

## Uso:
`/melhoria <descricao em linguagem natural do que quer melhorar>`

## Acao:
Executa a skill `melhoria` para investigar o codigo (preferencialmente via `code-review-graph`, com fallback universal para Grep/Glob/Read), atribuir uma Nota Atual (0-10) sempre com evidencia real, e gerar o par `.html`+`.json` do relatorio. Se o pedido referenciar um plano ja existente em `docs/planos/`, reanalisa o codigo real e compara com o que o plano previa (Nota Anterior -> Nota Nova, e um veredito feito/parcial/nao-feito por item). Ao final, sugere iniciar o `/plan` (relatorio novo) ou gravar a nota nova no plano existente — nunca dispara nenhum dos dois sozinho.

Equivalente CLI: `python ecossistema.py melhoria init --pedido "<texto>" [--nome ...] [--nota-atual ...] [--evidencia ...] [--resumo ...] [--achados ...] [--riscos ...] [--recomendacao ...] [--plano-existente <caminho> [--item <NN>]] [--itens-avaliados "<item>::<feito|parcial|nao-feito>::<justificativa>" ...]`
