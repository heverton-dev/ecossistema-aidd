# 05 — Database: asyncpg para Postgres Async

## Nota Atual: 8/10 | Nota Alvo: 9/10 | Prioridade: BAIXA

## Evidência da Nota Atual
- SQLite WAL + PostgreSQL 16 (poliglota Bridge)
- SQLAlchemy 2.x (async engines suportados)
- psycopg2 para Postgres (síncrono)
- Alembic para migrations
- sqlglot para DDL translation

## O que será implementado
1. Adicionar `asyncpg` em `requirements.txt`
2. Criar `AsyncPostgresAdapter` na bridge `database.py`
3. Manter `PostgresAdapter` síncrono como fallback
4. AsyncEngine para PostgreSQL via `create_async_engine("postgresql+asyncpg://...")`

## Arquivos afetados
- `requirements.txt` (adicionar `asyncpg`)
- `tools/aidd-master/templates/v2/database.py` (adicionar AsyncPostgresAdapter)

## Critério de aceitação
- [ ] `await adapter.init_async()` funcional
- [ ] Queries async sem bloqueio do event loop
- [ ] Fallback síncrono continua funcionando

## Estimativa
- Esforço: Baixo (~0.5-1 dia)
- Impacto: +1 ponto (8→9)
