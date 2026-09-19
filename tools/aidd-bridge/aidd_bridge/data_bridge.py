# -*- coding: utf-8 -*-
"""
Data Bridge — Conversor e sanitizador determinístico de migrações Supabase
para PostgreSQL puro e container PostgREST (zero refatoração no frontend).
"""

import os
import re
from typing import List, Dict, Any

class DataBridge:
    # Migracoes que tocam essas tabelas so podem rodar DEPOIS que elas
    # existirem de verdade. Com GoTrue real (with_real_auth=True), quem cria
    # auth.users/auth.identities e o proprio GoTrue, num container separado,
    # so depois que o Postgres ja terminou seu init sincrono -- incluir essas
    # migracoes no init-db.sql (que roda ANTES de qualquer outro container
    # conseguir se conectar) sempre falha com "relation auth.users does not
    # exist" (achado real: projeto Lovable de producao "conexao-linktree",
    # migracao real de bootstrap de conta admin).
    AUTH_TABLE_PATTERN = re.compile(r"auth\.(users|identities)\b", re.IGNORECASE)

    def __init__(self, migrations: List[Dict[str, Any]]):
        self.migrations = migrations

    def _alguma_migracao_depende_de_auth_real(self) -> bool:
        """True se QUALQUER migracao referenciar auth.users/auth.identities
        diretamente -- nesse caso NENHUMA migracao de dominio pode rodar no
        init-db.sql sincrono (precisam todas esperar o GoTrue real existir).

        Importante: a decisao e tudo-ou-nada, nunca arquivo-por-arquivo.
        Migracoes reais frequentemente dependem umas das outras em ordem
        (um ENUM criado num arquivo, usado por uma tabela em outro arquivo
        posterior) -- separar so os arquivos que tocam auth.* e deixar os
        outros no init-db.sql quebra essa cadeia de dependencia sequencial
        (achado real: "type public.app_role does not exist", porque o tipo
        foi criado numa migracao adiada mas usado numa que ficou no init-db.sql).
        Adiar tudo junto, na MESMA ordem original, elimina essa classe de bug.
        """
        for mig in self.migrations:
            path = mig.get("path")
            if path and os.path.exists(path):
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    if self.AUTH_TABLE_PATTERN.search(f.read()):
                        return True
        return False

    def generate_post_auth_sql(self) -> str:
        """SQL de TODAS as migracoes de dominio, na ordem original -- roda
        depois que o GoTrue real ja criou auth.users/auth.identities. String
        vazia se nenhuma migracao tocar nessas tabelas (caso comum: nada
        precisa esperar, tudo roda no init-db.sql normalmente)."""
        if not self._alguma_migracao_depende_de_auth_real():
            return ""
        chunks = []
        for mig in self.migrations:
            path = mig.get("path")
            if path and os.path.exists(path):
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                sanitized = self.sanitize_sql(content)
                chunks.append(f"\n-- >>> INICIO (POS-AUTH): {mig.get('filename')} <<<\n{sanitized}\n-- >>> FIM: {mig.get('filename')} <<<\n")
        return "\n".join(chunks)

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
        # Schema real do auth.users/auth.identities do Supabase (colunas
        # oficiais, estaveis entre versoes), nao um stub minimo — achado
        # real (projeto Lovable de producao "conexao-linktree"): migracoes
        # reais fazem bootstrap de conta admin inserindo direto em
        # auth.users/auth.identities com colunas como instance_id,
        # encrypted_password (via pgcrypto crypt/gen_salt), raw_app_meta_data
        # etc. Um stub de 3 colunas (id/email/created_at) quebra qualquer
        # migracao real que faca isso, com "column ... does not exist".
        auth_table_block = "" if with_real_auth else """
CREATE TABLE IF NOT EXISTS auth.users (
    instance_id uuid,
    id uuid NOT NULL PRIMARY KEY DEFAULT gen_random_uuid(),
    aud varchar(255),
    role varchar(255),
    email varchar(255),
    encrypted_password varchar(255),
    email_confirmed_at timestamptz,
    invited_at timestamptz,
    confirmation_token varchar(255),
    confirmation_sent_at timestamptz,
    recovery_token varchar(255),
    recovery_sent_at timestamptz,
    email_change_token_new varchar(255),
    email_change varchar(255),
    email_change_sent_at timestamptz,
    last_sign_in_at timestamptz,
    raw_app_meta_data jsonb,
    raw_user_meta_data jsonb,
    is_super_admin boolean,
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now(),
    phone text,
    phone_confirmed_at timestamptz,
    phone_change text DEFAULT '',
    phone_change_token varchar(255) DEFAULT '',
    phone_change_sent_at timestamptz,
    email_change_token_current varchar(255) DEFAULT '',
    email_change_confirm_status smallint DEFAULT 0,
    banned_until timestamptz,
    reauthentication_token varchar(255) DEFAULT '',
    reauthentication_sent_at timestamptz,
    is_sso_user boolean NOT NULL DEFAULT false,
    deleted_at timestamptz,
    is_anonymous boolean NOT NULL DEFAULT false
);

CREATE TABLE IF NOT EXISTS auth.identities (
    id uuid NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    provider_id text NOT NULL,
    user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    identity_data jsonb NOT NULL,
    provider text NOT NULL,
    last_sign_in_at timestamptz,
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now(),
    email text GENERATED ALWAYS AS (lower(identity_data ->> 'email')) STORED,
    UNIQUE (provider_id, provider)
);
"""
        auth_grant_line = "" if with_real_auth else (
            "GRANT SELECT ON auth.users TO anon, authenticated, service_role;\n"
            "GRANT SELECT ON auth.identities TO anon, authenticated, service_role;\n"
        )

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

        migracoes_seguras = self.migrations
        if with_real_auth and self._alguma_migracao_depende_de_auth_real():
            migracoes_seguras = []

        for mig in migracoes_seguras:
            path = mig.get("path")
            if path and os.path.exists(path):
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    sanitized = self.sanitize_sql(content)
                    chunks.append(f"\n-- >>> INICIO: {mig.get('filename')} <<<\n{sanitized}\n-- >>> FIM: {mig.get('filename')} <<<\n")

        return "\n".join(chunks)