# ADR — Registro de Decisões de Arquitetura

Cada decisão que muda um contrato, um termo do `CONTEXT.md` ou uma regra do ecossistema vira um arquivo nesta pasta. Adaptado de `domain-modeling` (mattpocock/skills, licença MIT).

## Regras
- Nome do arquivo: `NNNN-titulo-curto.md` (4 dígitos em sequência, minúsculas, hífen). Ex.: `0001-sentido-de-ciclo.md`.
- Um ADR por decisão. Decisão trocada = ADR novo com status "Substitui NNNN"; o antigo passa a "Substituído por NNNN". Nunca apagar ADR.
- Só o usuário decide. O agente pode rascunhar o ADR com status "Proposto"; "Aceito" exige confirmação do usuário na conversa.
- Termo decidido: atualizar `CONTEXT.md` no mesmo commit (mover de "Ambiguidades sinalizadas" para "Linguagem").

## Formato

```markdown
# NNNN — Título curto

## Status
Proposto | Aceito | Substituído por NNNN | Substitui NNNN
Data: DD/MM/AAAA

## Contexto
O problema e as forças em jogo. Evidência (arquivo, commit, laudo).

## Decisão
O que foi decidido, em uma ou duas frases afirmativas.

## Consequências
O que muda, o que fica mais caro, o que precisa ser migrado.
```
