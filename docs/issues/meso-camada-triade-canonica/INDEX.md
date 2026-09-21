# Índice de Tickets — Meso-Camada da Tríade Canônica

> Títulos em PT-BR, especificações e critérios em inglês telegráfico imperativo.

## 📋 Backlog de Execução Sequencial

| # | ID | Ticket | Status | Bloqueado Por |
|---|---|---|---|---|
| 01 | `ISSUE-MESO-0001` | [Schema Canônico do Grafo Topológico VSA de Despacho](01-schema-grafo-topologico-vsa.md) | `ready-for-agent` | `[]` |
| 02 | `ISSUE-MESO-0002` | [Compilador de Grafo Topológico VSA no aidd-planner](02-compilador-dag-vsa-planner.md) | `ready-for-agent` | `[ISSUE-MESO-0001]` |
| 03 | `ISSUE-MESO-0003` | [Quality Gate G_DISPATCH_PIPELINE_VSA com Prova que Morde](03-quality-gate-dispatch-vsa-morde.md) | `ready-for-agent` | `[ISSUE-MESO-0001, ISSUE-MESO-0002]` |
| 04 | `ISSUE-MESO-0004` | [Motor de Despacho de Fatias em Git Worktrees Efêmeros](04-motor-dispatch-pipeline-worktrees.md) | `ready-for-agent` | `[ISSUE-MESO-0003]` |
| 05 | `ISSUE-MESO-0005` | [Roteadores Especialistas para as 3 Engines da Tríade](05-roteadores-especialistas-engines-triade.md) | `ready-for-agent` | `[ISSUE-MESO-0004]` |
| 06 | `ISSUE-MESO-0006` | [Barreira de Validação por Fatia e Fusão Convergente no aidd-master](06-barreira-validacao-convergencia-master.md) | `ready-for-agent` | `[ISSUE-MESO-0005]` |
| 07 | `ISSUE-MESO-0007` | [Integração no Orquestrador Síncrono e Comando CLI ecossistema.py](07-integracao-orquestrador-sincrono-cli.md) | `ready-for-agent` | `[ISSUE-MESO-0006]` |
| 08 | `ISSUE-MESO-0008` | [Skill Canônica Multi-Harness aidd-dispatch-runner e Encadeamento de Intake](08-skills-triade-intake-grill-spec-dispatch.md) | `ready-for-agent` | `[ISSUE-MESO-0007]` |
