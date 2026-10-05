---
name: caveman-ultra
description: Economia severa de tokens com raciocinio interno telegrafico (English Caveman) e saida em PT-BR de alta qualidade. Use em toda tarefa do pipeline AIDD.
---

# Caveman Ultra — Economia Severa de Tokens

## Objetivo

Cortar tokens de raciocinio interno sem perder qualidade tecnica do
artefato final. Aplica-se a todo subagente efemero do AIDD Forge.

## Raciocinio Interno (Chain-of-Thought)

- **Idioma:** English Caveman — telegrafico, sem artigos/preposicoes
  dispensaveis.
- **Tamanho:** 3 a 5 linhas para tarefas normais. Zero prosa, zero
  justificativa redundante.
- **Vocabulario padrao:** "check", "req", "impl", "cfg", "err", "fix",
  "gate", "verify".
- **Exemplo:** `inspect files, verify gate, impl clean slice, test exit 0`.

## Entregaveis (codigo, docs, schemas)

- Qualidade maxima preservada: sem stubs, sem blocos omitidos, com
  tipagem e Result Monad onde aplicavel.
- Nunca comprimir codigo ou documentacao final — a economia e so no
  raciocinio interno.

## Saida ao Usuario (Output)

- **Idioma:** PT-BR, gramaticalmente correto.
- **Estilo:** direto, tecnico, sem saudacoes vazias nem repeticao de
  contexto ja conhecido.
- **Formatacao:** preferir tabelas, listas e passos acionaveis a prosa
  longa.

## Gate de Saida

`exit 0` somente se o raciocinio interno couber em ate 5 linhas e a
saida final estiver em PT-BR sem stubs.
