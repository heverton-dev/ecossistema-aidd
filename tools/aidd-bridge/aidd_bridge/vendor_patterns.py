# -*- coding: utf-8 -*-
"""
Fonte unica dos padroes de vendor lock-in (deteccao em G_BRIDGE_VENDOR_LOCKIN
e reescrita em FrontendLiberator) para as duas pontas nunca divergirem sobre
o que conta como "preso a nuvem proprietaria".
"""

import re

CLOUD_URL_PATTERNS = [
    (re.compile(r"https?://[a-zA-Z0-9_\-]+\.supabase\.co(?!\w)", re.IGNORECASE), "URL hardcoded do Supabase Cloud encontrada"),
    (re.compile(r"https?://[a-zA-Z0-9_\-]+\.firebaseio\.com", re.IGNORECASE), "URL hardcoded do Firebase Cloud encontrada"),
]

EXTENSOES_VARREDURA = {".ts", ".tsx", ".js", ".jsx", ".json", ".sql", ".env"}

# Reconhece a chave publica (anon/publishable) do Supabase atribuida a uma
# const cujo nome sinaliza a intencao (padrao real de export Lovable/v0/Bolt).
ANON_KEY_ASSIGNMENT = re.compile(
    r'(const\s+\w*(?:ANON|PUBLISHABLE)\w*\s*=\s*)["\']([^"\']+)["\']',
    re.IGNORECASE,
)

SUPABASE_URL_LITERAL = re.compile(r'["\']https?://[a-zA-Z0-9_\-]+\.supabase\.co["\']', re.IGNORECASE)
