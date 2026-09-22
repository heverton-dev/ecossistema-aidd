# Índice de Tickets — Usabilidade do Ecossistema-AIDD

> Títulos em PT-BR, especificações e critérios em inglês teleográf imperativo.
> Fonte: `docs/melhorias/22-09-2026_RELATORIO-ACHADOS-USABILIDADE-ECOSSISTEMA-AIDD.md` (A1–A9).
> Especificação: `docs/melhorias/22-09-2026_especificacao-tecnica-usabilidade-ecossistema.md`.

## 📋 Backlog de Execução Sequencial

| # | ID | Ticket | Achado | Prioridade | Status | Bloqueado Por |
|---|---|---|---|---|---|---|
| 01 | `ISSUE-USA-0001` | [Alias de sincronização e docs canônicos](01-alias-sync-docs-canonicos.md) | A1 | P0 | `done` | `[]` |
| 02 | `ISSUE-USA-0002` | [Helper determinístico de posicionamento da entrega](02-helper-posicionamento-entrega.md) | A6 | P0 | `done` | `[]` |
| 03 | `ISSUE-USA-0003` | [Entrega fora do clone e aninhamento achatado](03-entrega-fora-clone-achatada.md) | A4 | P0 | `done` | `[ISSUE-USA-0002]` |
| 04 | `ISSUE-USA-0004` | [Perfil de linguagem leigo e GEMINI.md](04-perfil-linguagem-leigo.md) | A2 | P0 | `done` | `[]` |
| 05 | `ISSUE-USA-0005` | [Ponto de entrada único da entrega](05-ponto-entrada-unico.md) | A5 | P1 | `done` | `[ISSUE-USA-0003]` |
| 06 | `ISSUE-USA-0006` | [Pacote core enxuto de distribuição](06-pacote-core-enxuto.md) | A3 | P1 | `done` | `[]` |
| 07 | `ISSUE-USA-0007` | [Template duplo de encerramento](07-template-duplo-encerramento.md) | A9 | P1 | `done` | `[]` |
| 08 | `ISSUE-USA-0008` | [Varredura anti-lock-in completa](08-varredura-anti-lockin.md) | A7 | P2 | `done` | `[]` |
| 09 | `ISSUE-USA-0009` | [Topologia Git padrão](09-topologia-git-padrao.md) | A8 | P2 | `done` | `[ISSUE-USA-0003]` |

## Mapa de Rastreabilidade

```text
A1 ──► 0001 ──► G_SYNC_CMD_ROT
A6 ──► 0002 ──► G_LAYOUT_ENTREGA ──┐
A4 ──► 0003 ◄──────────────────────┘──► card entrega + flatten
A2 ──► 0004 ──► G_USER_FACING_PTBR + perfil leigo
A5 ──► 0005 ◄── 0003 ──► README-USUARIO + umbrella
A3 ──► 0006 ──► G_PACOTE_CORE
A9 ──► 0007 ──► G_RESUMO_USUARIO
A7 ──► 0008 ──► G_ANT_LOCKIN_LEGADO
A8 ──► 0009 ◄── 0003 ──► git topology E2E
```

## Ondas de Execução (recomendadas)

| Onda | Tickets | Foco |
|---|---|---|
| P0 | 0001, 0002, 0004 (paralelo conceitual; serial por Lei #7) | Fricção imediata do teste |
| P0b | 0003 | Topologia de entrega (depende de 0002) |
| P1 | 0005, 0006, 0007 | Entrega compreensível e enxuta |
| P2 | 0008, 0009 | Proteções e fronteiras |
| Fechamento | — | `python ecossistema.py audit` + E2E usabilidade (clone→1 comando→1 URL) |
