# Índice de Tickets — Pipeline de Orquestração Tríade

> Títulos em PT-BR, especificações e critérios em inglês telegráfico imperativo.

## 📋 Backlog de Execução Sequencial

| # | ID | Ticket | Status | Bloqueado Por |
|---|---|---|---|---|
| 01 | `ISSUE-PIPE-0001` | [Schema Canônico de Contrato de Handoff de Execução](01-schema-contrato-handoff-execucao.md) | `done` | `[]` |
| 02 | `ISSUE-PIPE-0002` | [Quality Gate G_PIPELINE_HANDOFF com Prova que Morde](02-quality-gate-pipeline-handoff.md) | `done` | `[ISSUE-PIPE-0001]` |
| 03 | `ISSUE-PIPE-0003` | [Motor de Execução de Fases em Git Worktrees e Join Barrier](03-motor-execucao-worktrees-join-barrier.md) | `done` | `[ISSUE-PIPE-0002]` |
| 04 | `ISSUE-PIPE-0004` | [Compilador de Tickets de Planos Markdown para Handoff JSON](04-compilador-tickets-plano-para-handoff.md) | `done` | `[ISSUE-PIPE-0001]` |
| 05 | `ISSUE-PIPE-0005` | [Exportador Nativo do aidd-planner para o Schema de Pipeline](05-exportador-planner-para-pipeline.md) | `done` | `[ISSUE-PIPE-0001]` |
| 06 | `ISSUE-PIPE-0006` | [Acionamento Tríade Universal: CLI, Slash Command e Skill Runner](06-triade-acionamento-cli-slash-skill.md) | `done` | `[ISSUE-PIPE-0003, ISSUE-PIPE-0004, ISSUE-PIPE-0005]` |
| 07 | `ISSUE-PIPE-0007` | [Integração Completa de Ponta a Ponta e Testes de Regressão](07-integracao-e-testes-end-to-end.md) | `done` | `[ISSUE-PIPE-0006]` |
