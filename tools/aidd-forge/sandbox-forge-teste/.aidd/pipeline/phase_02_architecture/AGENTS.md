# AGENTS.md — Fase 02: Architecture

## Objetivo

Modelar os contratos de dados da fatia como schemas **JSON Schema Draft
2020-12**. O artefato desta fase é o contrato formal que a fase de
implementação vai satisfazer — nunca código de implementação.

## Escopo Permitido

- Criar/editar arquivos `*.schema.json` nesta pasta, via **Schemas MCP**
  (único MCP habilitado nesta fase).
- Validar cada schema contra o meta-schema Draft 2020-12 antes de salvar.

## Escopo Proibido

- Não escrever código de implementação nem testes.
- Não usar nenhum MCP além do Schemas (sem Filesystem genérico, sem
  Database).
- Não avançar para `phase_03_implementation` com schema inválido.

## Gate de Saída

`exit 0` somente se todo `*.schema.json` desta pasta validar contra o
meta-schema `https://json-schema.org/draft/2020-12/schema`.
