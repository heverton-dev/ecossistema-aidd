# AGENTS.md — Fase 03: Implementation

## Objetivo

Implementar a fatia de código que satisfaz o schema de
`phase_02_architecture`, usando **Result Monad** (nunca exceções para
fluxo de controle esperado) e cobertura via **pytest** real, sem stubs.

## Escopo Permitido

- Escrever código de implementação e testes `pytest` nesta pasta.
- Acessar dados via **Database MCP** (único MCP habilitado nesta fase).
- Rodar `pytest` localmente e corrigir falhas antes de finalizar.

## Escopo Proibido

- Não redefinir contratos da fase de arquitetura.
- Não usar nenhum MCP além do Database (sem Filesystem genérico, sem
  Schemas).
- Não entregar função com `pass`, `TODO` ou corpo vazio (stub).

## Gate de Saída

`exit 0` somente se `pytest` retornar 100% de sucesso e nenhuma função
pública tiver corpo de stub.
