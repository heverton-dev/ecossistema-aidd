# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD BRIDGE — DETERMINISTIC SQL TRANSPILER & SANITIZER
=============================================================================
Converte dialetos de schema e dados originados do Supabase / Lovable em
scripts PostgreSQL 16 ANSI puros, neutralizando hooks de nuvem e
assegurando compatibilidade com PostgREST self-hosted com zero alucinacao.
"""

import re
from typing import Tuple


class SQLTranspiler:
    """Transpilador deterministico de scripts SQL para PostgreSQL puro."""

    @staticmethod
    def transpile_supabase_to_postgres(sql_script: str) -> Tuple[str, int]:
        """Converte comandos de schema e triggers com contagem de substituicoes."""
        modifications_count = 0

        # 1. Remover extensoes proprietarias ou desnecessarias em ambiente self-hosted
        clean_sql, n1 = re.subn(
            r'CREATE\s+EXTENSION\s+IF\s+NOT\s+EXISTS\s+"?(vault|pg_net|pg_graphql|pgjwt)"?\s*;?',
            '-- [Transpiled: Cloud extension neutralized]',
            sql_script,
            flags=re.IGNORECASE
        )
        modifications_count += n1

        # 2. Ajustar referencias a schemas internos supabase para public/auth
        clean_sql, n2 = re.subn(
            r'auth\.users',
            'public.users',
            clean_sql,
            flags=re.IGNORECASE
        )
        modifications_count += n2

        # 3. Remover hooks de webhook do realtime supabase
        clean_sql, n3 = re.subn(
            r'CREATE\s+TRIGGER\s+.*?\s+AFTER\s+.*?\s+ON\s+.*?\s+FOR\s+EACH\s+ROW\s+EXECUTE\s+FUNCTION\s+supabase_realtime\..*?;',
            '-- [Transpiled: Realtime webhook hook neutralized]',
            clean_sql,
            flags=re.IGNORECASE | re.DOTALL
        )
        modifications_count += n3

        return clean_sql, modifications_count
