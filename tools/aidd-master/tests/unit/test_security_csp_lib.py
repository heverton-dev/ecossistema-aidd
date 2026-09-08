# -*- coding: utf-8 -*-
"""
Testes unitarios para o SecurityService com biblioteca secure (secure.py).
Atende ao criterio de Fase2-Seg2 (NIH #9):
- CSP definido via lib, nao string literal.
- Templates gerados usam a lib.
- Prevencao contra regressao de CSP relaxado.
"""

import ast
import os
import pytest
import secure
from pathlib import Path

from src.core.security import SecurityService


def test_csp_construido_via_biblioteca_secure():
    """Valida que build_csp() retorna um objeto ContentSecurityPolicy da lib secure."""
    csp = SecurityService.build_csp()
    assert isinstance(csp, secure.ContentSecurityPolicy)
    assert csp.header_name == "Content-Security-Policy"

    val = csp.header_value
    assert "default-src 'self'" in val
    assert "script-src" in val
    assert "'unsafe-eval'" not in val, "VULNERABILIDADE: 'unsafe-eval' proibido no CSP"
    assert "style-src" in val
    assert "font-src" in val
    assert "img-src" in val
    assert "connect-src" in val


def test_csp_custom_directives():
    """Valida que diretivas customizadas podem ser adicionadas atraves do builder."""
    csp = SecurityService.build_csp(custom_directives={"frame_ancestors": "'none'"})
    val = csp.header_value
    assert "frame-ancestors 'none'" in val


def test_security_headers_contem_todos_os_headers_owasp():
    """Valida que get_security_headers() gera o dicionario completo via Secure."""
    headers = SecurityService.get_security_headers()
    assert isinstance(headers, dict)

    obrigatorios = [
        ("X-Content-Type-Options", "nosniff"),
        ("X-Frame-Options", "DENY"),
        ("X-XSS-Protection", "1; mode=block"),
        ("Referrer-Policy", "strict-origin-when-cross-origin"),
        ("Strict-Transport-Security", "max-age=63072000; includeSubDomains; preload"),
        ("Permissions-Policy", "geolocation=(), microphone=(), camera=()"),
    ]
    for h, expected in obrigatorios:
        assert h in headers, f"Header obrigatorio ausente: {h}"
        assert expected in headers[h], f"Valor inesperado para {h}: {headers[h]}"

    assert "Content-Security-Policy" in headers
    csp_val = headers["Content-Security-Policy"]
    assert "'unsafe-eval'" not in csp_val


def test_templates_usam_biblioteca_secure():
    """Garante que tanto templates/core quanto templates/v2 usam a biblioteca secure via AST."""
    root = Path(__file__).resolve().parent.parent.parent
    caminhos = [
        root / "templates" / "core" / "security.py",
        root / "templates" / "v2" / "security.py",
    ]

    for p in caminhos:
        assert p.exists(), f"Template nao encontrado: {p}"
        conteudo = p.read_text(encoding="utf-8")
        arvore = ast.parse(conteudo, filename=str(p))

        imports = []
        for node in ast.walk(arvore):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                imports.append(node.module)

        assert "secure" in imports, f"{p} nao importa a biblioteca secure"
        assert "build_csp" in conteudo, f"{p} nao define ou usa build_csp"
