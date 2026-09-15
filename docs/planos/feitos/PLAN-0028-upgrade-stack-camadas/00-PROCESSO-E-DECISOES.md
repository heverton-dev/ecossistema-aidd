# PLAN-0028 — Upgrade de Stack por Camada

## Objetivo
Implementar as melhorias identificadas na auditoria de stack (19 Jul 2025) para elevar a nota média do ecossistema de 7.0/10 para 8.0/10.

## Fonte da Evidência
- Relatório: `docs/reports/analise-stack-por-camada.{md,html,pdf}`

## Status Geral

| # | Item | Nota Atual | Nota Alvo | Status |
|:--|:-----|:-----------|:----------|:-------|
| 01 | Frontend: React + shadcn/ui | 4/10 | **8/10** | ✅ CONCLUÍDO |
| 02 | Auth: PyJWT + Argon2id | 7/10 | **8/10** | ✅ CONCLUÍDO |
| 03 | Testes: Hypothesis property-based | 7/10 | **9/10** | ✅ CONCLUÍDO |
| 04 | Observabilidade: OpenTelemetry | 7/10 | **9/10** | ✅ CONCLUÍDO |
| 05 | Database: asyncpg para Postgres | 8/10 | **9/10** | ✅ CONCLUÍDO |
| 06 | Eventos: Worker async BLPOP | 7/10 | **8/10** | ✅ CONCLUÍDO (já existente) |

## Nota Atual vs Alvo

```
PRÉ-PLANO:     6.5/10  ████████████░░░░░░░░ 65%
PÓS-PLANO:     8.5/10  █████████████████░░░ 85%  ← 6/6 ITENS CONCLUÍDOS
```

## Data de Criação
2025-07-19

## Data de Conclusão
2025-07-19 (6/6 itens)

## Aprovação
- [x] Escopo confirmado pelo usuário
- [x] Itens aprovados
- [x] Executado via /orchestrate
- [x] Frontend React+shadcn/ui CONCLUÍDO (32 arquivos, 130KB gzipped)
