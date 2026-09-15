# PLAN-0028 — Upgrade de Stack por Camada

## Objetivo
Implementar as melhorias identificadas na auditoria de stack (19 Jul 2025) para elevar a nota média do ecossistema de 7.0/10 para 8.0/10.

## Fonte da Evidência
- Relatório: `docs/reports/analise-stack-por-camada.{md,html,pdf}`
- Implementações parciais já realizadas: `server_fastapi.py` (Backend 5→8), `metrics.py` dual-path (Monitoramento 6→7)

## Status Geral

| # | Item | Nota Atual | Nota Alvo | Status |
|:--|:-----|:-----------|:----------|:-------|
| 01 | Frontend: React + shadcn/ui | 4/10 | 8/10 | ⏳ |
| 02 | Auth: PyJWT + Argon2id | 7/10 | 8/10 | ⏳ |
| 03 | Testes: Hypothesis property-based | 7/10 | 9/10 | ⏳ |
| 04 | Observabilidade: OpenTelemetry | 7/10 | 9/10 | ⏳ |
| 05 | Database: asyncpg para Postgres | 8/10 | 9/10 | ⏳ |
| 06 | Eventos: Worker async BLPOP | 7/10 | 8/10 | ⏳ |

## Nota Atual vs Alvo

```
ANTES (pré-impl):  6.5/10  ████████████░░░░░░░░ 65%
AGORA (pós-impl):  7.0/10  █████████████░░░░░░░ 70%
META (pós-plano):  8.0/10  ████████████████░░░░ 80%
```

## Data de Criação
2025-07-19

## Aprovação
- [ ] Escopo confirmado pelo usuário
- [ ] Itens aprovados
- [ ] Pronto para `/orchestrate`
