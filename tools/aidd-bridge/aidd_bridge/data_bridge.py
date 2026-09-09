# -*- coding: utf-8 -*-
"""
Data Bridge — Conversor e sanitizador determinístico de migrações Supabase
para PostgreSQL puro e container PostgREST (zero refatoração no frontend).
"""

import os
import re
from typing import List, Dict, Any

class DataBridge:
    def __init__(self, migrations: List[Dict[str, Any]]):
        self.migrations = migrations

    def sanitize_sql(self, sql_content: str) -> str:
        """
        Sanitiza scripts SQL do Supabase para rodar em qualquer PostgreSQL padrão.
        """
        sanitized = sql_content

        # Remove chamadas para schemas ou funções proprietárias de nuvem
        # ex: supabase_vault, pg_net, cron, etc.
        patterns_to_comment = [
            r'(?i)create\s+extension\s+if\s+not\s+exists\s+["\']?(supabase_vault|pg_net|pg_graphql|vault)["\']?[^;]*;',
            r'(?i)alter\s+publication\s+supabase_realtime\s+add\s+table[^;]*;',
            r'(?i)comment\s+on\s+schema\s+["\']?auth["\']?[^;]*;'
        ]

        for p in patterns_to_comment:
            sanitized = re.sub(p, r'-- [AIDD-BRIDGE REMOVED PROPRIETARY CLOUD HOOK]\n-- \g<0>', sanitized)

        return sanitized

    def generate_consolidated_init_sql(self) -> str:
        """
        Gera um script init-db.sql consolidado com os schemas básicos,
        papéis de acesso do PostgREST (anon, authenticated, web_anon) e tabelas.
        """
        header = """-- =============================================================================
-- AIDD-BRIDGE: CONSOLIDATED POSTGRESQL INITIALIZATION
-- Gerado determinísticamente para execução em PostgreSQL Puro / Self-Hosted VPS
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Roles para PostgREST (emulação Supabase REST API)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'anon') THEN
        CREATE ROLE anon NOLOGIN;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'authenticated') THEN
        CREATE ROLE authenticated NOLOGIN;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'authenticator') THEN
        CREATE ROLE authenticator NOINHERIT LOGIN PASSWORD 'aidd_authenticator_pwd';
    END IF;
END
$$;

GRANT anon TO authenticator;
GRANT authenticated TO authenticator;

-- Schema public grants
GRANT USAGE ON SCHEMA public TO anon;
GRANT USAGE ON SCHEMA public TO authenticated;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO anon;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO authenticated;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO anon;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO authenticated;

-- =============================================================================
-- MIGRAÇÕES DE DOMÍNIO
-- =============================================================================
"""
        chunks = [header]

        for mig in self.migrations:
            path = mig.get("path")
            if path and os.path.exists(path):
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    sanitized = self.sanitize_sql(content)
                    chunks.append(f"\n-- >>> INICIO: {mig.get('filename')} <<<\n{sanitized}\n-- >>> FIM: {mig.get('filename')} <<<\n")

        return "\n".join(chunks)