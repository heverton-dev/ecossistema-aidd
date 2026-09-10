# -*- coding: utf-8 -*-
"""
AuthMigrator — Migra contas reais (auth.users + auth.identities) de um
Postgres de origem (Supabase Cloud, ou qualquer instância GoTrue compatível)
para o banco self-hosted gerado pelo aidd-bridge.

Preserva o hash de senha (bcrypt) tal como está — ninguém precisa trocar de
senha. A operação é sempre aditiva e idempotente: nunca sobrescreve nem
apaga uma conta que já exista no destino (ON CONFLICT DO NOTHING), e pode
ser rodada de novo com segurança.

Como as colunas de auth.users/auth.identities variam entre versões do
GoTrue, a migração usa apenas a interseção de colunas presentes em origem
E destino — nunca assume um schema fixo.
"""

from typing import Any, Dict, List, Optional, Set

import psycopg2
import psycopg2.extras


def plan_migration(
    source_rows: List[Dict[str, Any]],
    existing_target_ids: Set[str],
    id_key: str = "id",
) -> Dict[str, Any]:
    """
    Decide quais linhas de origem precisam ser inseridas no destino.
    Função pura (sem I/O) para poder ser testada sem um Postgres real.
    """
    to_insert = [r for r in source_rows if str(r[id_key]) not in existing_target_ids]
    skipped_existing = [r for r in source_rows if str(r[id_key]) in existing_target_ids]
    return {
        "total_source": len(source_rows),
        "to_insert": to_insert,
        "skipped_existing": skipped_existing,
    }


class AuthMigrator:
    def __init__(self, source_dsn: str, target_dsn: str):
        self.source_dsn = source_dsn
        self.target_dsn = target_dsn

    def _connect(self, dsn: str):
        return psycopg2.connect(dsn)

    def _table_columns(self, conn, schema: str, table: str) -> Set[str]:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema=%s AND table_name=%s",
                (schema, table),
            )
            return {r[0] for r in cur.fetchall()}

    def _common_columns(self, source_conn, target_conn, schema: str, table: str, required: Set[str]) -> List[str]:
        src_cols = self._table_columns(source_conn, schema, table)
        tgt_cols = self._table_columns(target_conn, schema, table)
        common = src_cols & tgt_cols
        missing = required - common
        if missing:
            raise RuntimeError(
                f'{schema}.{table}: colunas obrigatórias ausentes na interseção '
                f'origem/destino: {sorted(missing)}'
            )
        return sorted(common)

    def _fetch_rows(self, conn, schema: str, table: str, columns: List[str]) -> List[Dict[str, Any]]:
        cols_sql = ", ".join(f'"{c}"' for c in columns)
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(f'SELECT {cols_sql} FROM "{schema}"."{table}"')
            return [dict(r) for r in cur.fetchall()]

    def _existing_ids(self, conn, schema: str, table: str, id_column: str) -> Set[str]:
        with conn.cursor() as cur:
            cur.execute(f'SELECT "{id_column}" FROM "{schema}"."{table}"')
            return {str(r[0]) for r in cur.fetchall()}

    def _insert_rows(self, conn, schema: str, table: str, rows: List[Dict[str, Any]], columns: List[str], conflict_column: str) -> int:
        if not rows:
            return 0
        cols_sql = ", ".join(f'"{c}"' for c in columns)
        placeholders = ", ".join(["%s"] * len(columns))
        sql = (
            f'INSERT INTO "{schema}"."{table}" ({cols_sql}) '
            f'VALUES ({placeholders}) '
            f'ON CONFLICT ("{conflict_column}") DO NOTHING'
        )
        with conn.cursor() as cur:
            for row in rows:
                cur.execute(sql, [row.get(c) for c in columns])
        conn.commit()
        return len(rows)

    def _migrate_users(self, source_conn, target_conn, dry_run: bool) -> Dict[str, Any]:
        required = {"id", "email", "encrypted_password"}
        columns = self._common_columns(source_conn, target_conn, "auth", "users", required)
        source_rows = self._fetch_rows(source_conn, "auth", "users", columns)
        existing_ids = self._existing_ids(target_conn, "auth", "users", "id")
        plan = plan_migration(source_rows, existing_ids, id_key="id")

        inserted = 0
        if not dry_run:
            inserted = self._insert_rows(target_conn, "auth", "users", plan["to_insert"], columns, conflict_column="id")

        return {
            "total_source": plan["total_source"],
            "inserted": inserted,
            "would_insert": len(plan["to_insert"]),
            "skipped_existing": len(plan["skipped_existing"]),
            "columns_migrated": columns,
        }

    def _migrate_identities(self, source_conn, target_conn, dry_run: bool) -> Dict[str, Any]:
        # GoTrue renomeou a coluna de identidade de "id" para "identity_id"
        # em versões mais novas — descobre qual existe na origem.
        src_cols = self._table_columns(source_conn, "auth", "identities")
        id_col = "identity_id" if "identity_id" in src_cols and "id" not in src_cols else "id"

        try:
            required = {id_col, "user_id", "provider"}
            columns = self._common_columns(source_conn, target_conn, "auth", "identities", required)
        except RuntimeError as e:
            return {"skipped_incompatible": str(e), "total_source": 0, "inserted": 0, "would_insert": 0, "skipped_existing": 0}

        source_rows = self._fetch_rows(source_conn, "auth", "identities", columns)
        existing_ids = self._existing_ids(target_conn, "auth", "identities", id_col)
        plan = plan_migration(source_rows, existing_ids, id_key=id_col)

        inserted = 0
        if not dry_run:
            inserted = self._insert_rows(target_conn, "auth", "identities", plan["to_insert"], columns, conflict_column=id_col)

        return {
            "total_source": plan["total_source"],
            "inserted": inserted,
            "would_insert": len(plan["to_insert"]),
            "skipped_existing": len(plan["skipped_existing"]),
            "columns_migrated": columns,
        }

    def migrate(self, dry_run: bool = True) -> Dict[str, Any]:
        source_conn = self._connect(self.source_dsn)
        target_conn = self._connect(self.target_dsn)
        try:
            users_report = self._migrate_users(source_conn, target_conn, dry_run)
            identities_report = self._migrate_identities(source_conn, target_conn, dry_run)
            return {"dry_run": dry_run, "users": users_report, "identities": identities_report}
        finally:
            source_conn.close()
            target_conn.close()
