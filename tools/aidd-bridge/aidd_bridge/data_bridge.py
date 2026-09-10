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

        # Remove chamadas para extensões ou publicações de nuvem proprietárias
        patterns_to_comment = [
            r'(?i)create\s+extension\s+if\s+not\s+exists\s+["\']?(supabase_vault|pg_net|pg_graphql|vault)["\']?[^;]*;',
            r'(?i)alter\s+publication\s+supabase_realtime\s+add\s+table[^;]*;',
            r'(?i)comment\s+on\s+schema\s+["\']?auth["\']?[^;]*;'
        ]

        for p in patterns_to_comment:
            sanitized = re.sub(p, r'-- [AIDD-BRIDGE REMOVED PROPRIETARY CLOUD HOOK]\n-- \g<0>', sanitized)

        return sanitized

    def generate_consolidated_init_sql(self, with_real_auth: bool = False) -> str:
        """
        Gera um script init-db.sql consolidado com os schemas básicos,
        papéis de acesso do PostgREST (anon, authenticated, authenticator),
        emulação do schema auth (auth.users, auth.uid(), auth.role()) e tabelas.

        with_real_auth: quando True, o pacote de deploy inclui um GoTrue real
        (docker-compose.swarm.yml gerado pelo DevOpsPackager). Nesse caso a tabela
        auth.users NÃO é criada aqui — GoTrue cria a sua própria (com colunas como
        instance_id) na primeira subida. Criar a tabela emulada antes disso faz o
        "CREATE TABLE IF NOT EXISTS" do GoTrue virar no-op sobre um schema incompatível,
        e a migração dele falha com "column instance_id does not exist".
        Quando False (padrão, modo simples sem GoTrue), a tabela emulada é criada
        normalmente para permitir FKs/RLS via PostgREST puro.
        """
        auth_table_block = "" if with_real_auth else """
CREATE TABLE IF NOT EXISTS auth.users (
    id uuid NOT NULL PRIMARY KEY DEFAULT gen_random_uuid(),
    email text,
    created_at timestamptz DEFAULT now()
);
"""
        auth_grant_line = "" if with_real_auth else "GRANT SELECT ON auth.users TO anon, authenticated, service_role;\n"

        header = f"""-- =============================================================================
-- AIDD-BRIDGE: CONSOLIDATED POSTGRESQL INITIALIZATION
-- Gerado determinísticamente para execução em PostgreSQL Puro / Self-Hosted VPS
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =============================================================================
-- EMULAÇÃO DO SCHEMA AUTH (SUPABASE COMPATIBILITY LAYER)
-- Permite que Foreign Keys (REFERENCES auth.users) e RLS (auth.uid()) funcionem nativamente
-- =============================================================================
CREATE SCHEMA IF NOT EXISTS auth;
{auth_table_block}
-- Lê o claim tanto do estilo antigo do PostgREST (uma GUC por claim,
-- "request.jwt.claim.<nome>") quanto do estilo atual (PostgREST >= 11,
-- uma única GUC JSON "request.jwt.claims"). PGRST_DB_USE_LEGACY_GUCS foi
-- removido nas versões recentes, então depender só da GUC antiga faz
-- auth.uid() sempre retornar NULL e todo RLS baseado nela travar o
-- acesso do próprio usuário autenticado.
CREATE OR REPLACE FUNCTION auth.uid() RETURNS uuid AS $$
  SELECT COALESCE(
    NULLIF(current_setting('request.jwt.claim.sub', true), ''),
    (NULLIF(current_setting('request.jwt.claims', true), '')::jsonb ->> 'sub')
  )::uuid;
$$ LANGUAGE sql STABLE;

CREATE OR REPLACE FUNCTION auth.role() RETURNS text AS $$
  SELECT COALESCE(
    NULLIF(current_setting('request.jwt.claim.role', true), ''),
    (NULLIF(current_setting('request.jwt.claims', true), '')::jsonb ->> 'role')
  )::text;
$$ LANGUAGE sql STABLE;

CREATE OR REPLACE FUNCTION auth.email() RETURNS text AS $$
  SELECT COALESCE(
    NULLIF(current_setting('request.jwt.claim.email', true), ''),
    (NULLIF(current_setting('request.jwt.claims', true), '')::jsonb ->> 'email')
  )::text;
$$ LANGUAGE sql STABLE;

-- auth.jwt() — devolve o crachá (token) inteiro como JSON, igual a Supabase
-- real. Muitas políticas de RLS geradas pela Lovable usam isso pra ler dado
-- extra do usuário (ex: auth.jwt() -> 'app_metadata' ->> 'empresa_id'), não
-- só uid/role/email. Sem essa função, qualquer política que a use trava com
-- "function auth.jwt() does not exist" assim que alguém tenta acessar.
CREATE OR REPLACE FUNCTION auth.jwt() RETURNS jsonb AS $$
  SELECT COALESCE(NULLIF(current_setting('request.jwt.claims', true), ''), '{{}}')::jsonb;
$$ LANGUAGE sql STABLE;

-- Roles para PostgREST (emulação Supabase REST API)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'anon') THEN
        CREATE ROLE anon NOLOGIN;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'authenticated') THEN
        CREATE ROLE authenticated NOLOGIN;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'service_role') THEN
        CREATE ROLE service_role NOLOGIN BYPASSRLS;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'authenticator') THEN
        CREATE ROLE authenticator NOINHERIT LOGIN PASSWORD 'aidd_authenticator_pwd';
    END IF;
END
$$;

-- Garante BYPASSRLS mesmo se service_role já existia de uma execução anterior
-- sem essa flag. Sem isso, a "chave mestra" fica presa pelas mesmas travas de
-- RLS de um usuário comum — descoberto testando upload real no Storage: toda
-- criação de bucket/objeto é feita como service_role e trava com "new row
-- violates row-level security policy" até essa role poder ignorar RLS, igual
-- ao Supabase de verdade.
ALTER ROLE service_role BYPASSRLS;

GRANT anon TO authenticator;
GRANT authenticated TO authenticator;
GRANT service_role TO authenticator;

-- Grants nos schemas
GRANT USAGE ON SCHEMA public TO anon, authenticated, service_role;
GRANT USAGE ON SCHEMA auth TO anon, authenticated, service_role;
{auth_grant_line}
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO anon, authenticated, service_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO anon, authenticated, service_role;

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