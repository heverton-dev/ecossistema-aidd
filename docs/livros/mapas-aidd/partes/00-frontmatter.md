---
title: "Mapas do Ecossistema AIDD"
subtitle: "As peças, onde moram e o que falta consertar"
author:
  - Ecossistema AIDD
date: "26/09/2026"
lang: pt-BR
institute: "Ecossistema AIDD · mapa de peças, ciclo 01"
eyebrow: "LIVRO DIDÁTICO"
tagline: |
  Os 12 mapas visuais do ecossistema, na ordem de leitura, com os números medidos e cada defeito encontrado.
toc: true
toc-depth: 2
abstract: |
  Este livro percorre o ecossistema do geral para o particular: primeiro as leis, as fábricas e a receita
  que as liga; depois as peças do dia a dia; por fim os moldes, as máquinas e a oficina onde tudo é consertado.
  Cada capítulo corresponde a um mapa visual, na mesma ordem dos arquivos em docs/mapas-visuais/.

  Nada aqui é estimado. Os números vêm do catálogo de peças e os defeitos vêm do arquivo de achados, que
  hoje registra 1 achados em aberto, 0 sob suspeita e 14 resolvidos.
---

# Como ler este livro

## A quem este livro se destina

A quem desenvolve no ecossistema e precisa saber onde cada peça mora antes de mexer, e a quem vai decidir
o que consertar primeiro. Quem só quer a lista de defeitos pode ir direto ao Apêndice B.

## A estrutura

| Parte | Capítulos |
| :-------------------------------------- | :-------------------------------------------- |
| Parte I — As regras e as fábricas | 01, 02, 03 |
| Parte II — As peças do dia a dia | 04, 05, 06, 07, 08 |
| Parte III — O que vai junto e as máquinas | 09, 10 |
| Parte IV — A oficina | 11, 12 |

Cada capítulo responde sempre às mesmas quatro perguntas: o que é, os números de hoje, o que falta consertar e
de onde vieram as afirmações. O índice dos mapas, com o estado de cada um, está em `docs/mapas-visuais/mapa-00-indice.html`.

## As convenções visuais

```{=typst}
#painel("Números medidos")[
  Todo número deste livro foi lido do catálogo de peças no dia da geração. Se o catálogo mudar, o livro é
  gerado de novo pelo scripts/livro_mapas.py; nenhum número é digitado à mão.
]
```
