# Camada Database — Regras de Persistencia

> **Escopo:** Toda interacao com banco de dados (SQLite, PostgreSQL/Supabase) dentro do AIDD v5/v6.
> **Referencia:** `templates/core/database.py`, `templates/rules/04_cross_project.md`, `templates/rules/04_security.md`.

---

## 1. SQLite WAL Mode (Obrigatorio)

Toda conexao SQLite DEVE ativar WAL mode e pragmas de resiliencia:

```python
conn.execute("PRAGMA journal_mode=WAL;")
conn.execute("PRAGMA synchronous=NORMAL;")
conn.execute("PRAGMA busy_timeout=5000;")
conn.execute("PRAGMA foreign_keys=ON;")
```

- WAL mode e obrigatorio inclusive em testes unitarios (fixtures `tmp_path`).
- Nunca usar `journal_mode=DELETE` ou `synchronous=FULL` em producao.
- Conexoes devem usar `timeout=10.0` para evitar `SQLITE_BUSY`.

---

## 2. PostgreSQL / Supabase Support

- A deteccao do motor e feita via `DATABASE_URL`:
  - `sqlite:///...` -> `SQLiteAdapter`
  - `postgres://...` ou `postgresql://...` -> `PostgresAdapter`
- O `PostgresConnectionProxy` traduz automaticamente:
  - Placeholders `?` -> `%s`
  - `INTEGER PRIMARY KEY AUTOINCREMENT` -> `SERIAL PRIMARY KEY`
  - INSERTs sem `RETURNING` recebem `RETURNING id` automaticamente
- Modules gerados continuam usando `?` como placeholder — zero alteracao necessaria.
- Para Supabase, usar `postgresql://user:pass@host:5432/dbname?sslmode=require`.

---

## 3. Foreign Key Constraints (Obrigatorio)

- `PRAGMA foreign_keys=ON` em toda conexao SQLite.
- PostgreSQL: constraints `REFERENCES` definidas no DDL de criacao.
- Toda tabela DEVE declarar `FOREIGN KEY` para relacionamentos entre entidades.
- `ON DELETE CASCADE` apenas quando o dominio exige exclusao em cascata.
- `ON DELETE RESTRICT` como padrao seguro para evitar exclusao acidental.

---

## 4. RLSConnection com tenant_id Injection

Para arquiteturas multi-tenant:

```python
# Ativar RLS na tabela (PostgreSQL)
def enable_rls_tenant(cursor, table_name: str):
    cursor.execute(f"ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY;")
    cursor.execute(
        f"CREATE POLICY tenant_isolation ON {table_name} "
        f"USING (tenant_id = current_setting('app.current_tenant_id')::uuid);"
    )

# Injetar tenant_id na conexao
def set_tenant(cursor, tenant_id: str):
    cursor.execute(f"SET app.current_tenant_id = '{tenant_id}';")
```

- SQLite: RLS enforced na camada de aplicacao (filtro WHERE `tenant_id = ?`).
- PostgreSQL: RLS enforced via Row Level Security nativo.
- Todo `SELECT`, `UPDATE`, `DELETE` DEVE incluir filtro por `tenant_id`.
- O `tenant_id` e extraido do JWT claims e injetado no contexto da conexao.

---

## 5. Database MCP Integration Rules

- Toda operacao de persistencia DEVE ser exportada como ferramenta MCP (`/mcp`).
- Ferramentas MCP de banco usam `Result.ok()` / `Result.fail()` como retorno.
- Parametros de entrada validados antes de qualquer operacao SQL.
- Nenhuma query raw e exposta diretamente — apenas operacoes CRUD tipadas.
- Auditoria via `_audit_log` com hash encadeado SHA-256 em toda mutacao.

---

## 6. Cursor Support Requirements

- Usar `sqlite3.Row` como `row_factory` para acesso por nome de coluna.
- PostgreSQL: usar `RealDictCursor` do `psycopg2.extras`.
- Context manager obrigatorio (`with db.get_connection() as conn:`).
- Nunca manter conexoes abertas alem do bloco de uso.
- `cur.lastrowid` disponivel em ambos os drivers via `PostgresCursorProxy`.

---

## 7. Transactional Outbox Pattern

Toda mutacao de estado DEVE gravar o evento na mesma transacao:

```python
with db.get_connection() as conn:
    # 1. Mutacao de negocio
    conn.execute("INSERT INTO ...", params)
    # 2. Evento no outbox (mesma transacao)
    db.enqueue_outbox_event(conn, "modulo.entidade.criada", payload)
    conn.commit()
```

- Tabela `_outbox_events` com campos: `id`, `event_name`, `payload`, `status`, `criado_em`, `processado_em`.
- Worker de despacho (`outbox_worker.py`) processa eventos pendentes.
- Garantia: At-Least-Once Delivery com idempotencia no consumidor.

---

## 8. Schema Migrations

- Tabela `_schema_migrations` registra versoes aplicadas por modulo.
- `db.record_migration(module_name, version)` e idempotente (`ON CONFLICT DO UPDATE`).
- Migrations executadas automaticamente na inicializacao do modulo.
- Nunca alterar migrations ja aplicadas — criar nova migration incremental.

---

## Checklist de Auditoria Database

| # | Criterio | Gate |
|---|----------|------|
| 1 | WAL mode ativo em toda conexao SQLite | G_ESTRUTURA |
| 2 | `PRAGMA foreign_keys=ON` em toda conexao | G_ESTRUTURA |
| 3 | Context manager em toda operacao de banco | G_CONTRACTS |
| 4 | Parametros preparados (zero SQL injection) | G_SEGURANCA |
| 5 | Outbox events na mesma transacao da mutacao | G_TESTES |
| 6 | tenant_id filtrado em toda query multi-tenant | G_SEGURANCA |
| 7 | Audit log com hash encadeado em toda mutacao | G_QUALIDADE |
| 8 | Migrations idempotentes registradas | G_ESTRUTURA |
