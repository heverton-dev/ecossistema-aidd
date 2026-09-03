# AGENTS.md — Fase 01: Requirements

## Objetivo

Definir escopo e regras semânticas da fatia de trabalho: o que deve ser
construído, restrições de negócio e critérios de aceite. O artefato desta
fase é um documento de requisitos, nunca código.

## Escopo Permitido

- Ler e escrever arquivos de especificação (`spec.md`, `user-stories.md`)
  nesta pasta, via **Filesystem MCP** (único MCP habilitado nesta fase).
- Fazer perguntas de esclarecimento quando o pedido for ambíguo.

## Escopo Proibido

- Não escrever código de implementação nem schemas.
- Não usar nenhum MCP além do Filesystem (sem Database, sem Schemas).
- Não avançar para `phase_02_architecture` sem critérios de aceite
  explícitos no `spec.md`.

## Gate de Saída

`exit 0` somente se `spec.md` existir e contiver seção de critérios de
aceite não vazia.
