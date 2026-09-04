---
name: post-mortem
description: Investigacao de causa-raiz apos falha de gate ou incidente, usando a tecnica dos 5-Porques ate chegar na causa sistemica.
---

# Post-Mortem — Investigacao de Causa-Raiz (5-Porques)

## Objetivo

Quando um gate falha ou um incidente ocorre em producao, investigar a
causa raiz antes de qualquer correcao — nunca aplicar patch cego no
sintoma.

## Tecnica dos 5-Porques

1. Descrever o sintoma observado (o que quebrou, exit code, stack
   trace).
2. Perguntar "por que isso aconteceu?" e responder com fato verificavel
   (nao suposicao).
3. Repetir a pergunta sobre a resposta anterior, ate 5 niveis ou ate a
   causa deixar de ser tecnica e virar processo/decisao (ex: "gate nao
   cobria esse caso").
4. Parar antes se a causa raiz for encontrada em menos de 5 niveis —
   nao forcar niveis artificiais.

## Escopo Permitido

- Ler logs, diffs, historico de commits e relatorios de gate
  relacionados ao incidente.
- Escrever `post_mortem.md` com: sintoma, cadeia dos 5-Porques, causa
  raiz, acao corretiva recomendada.

## Escopo Proibido

- Nao aplicar a correcao diretamente nesta fase — apenas recomendar.
- Nao encerrar a investigacao na causa imediata (ex: "o teste falhou
  porque o valor estava errado") sem chegar na causa sistemica.

## Gate de Saida

`exit 0` somente se `post_mortem.md` existir com cadeia de causas
completa e uma acao corretiva concreta e acionavel.
