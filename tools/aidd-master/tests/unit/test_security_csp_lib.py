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


def _parse_csp(val):
    diretores = {}
    for parte in val.split(";"):
        parte = parte.strip()
        if not parte:
            continue
        chave, *valores = parte.split()
        diretores[chave] = " ".join(valores)
    return diretores


def test_script_src_sem_unsafe_inline():
    """PLAN-0025 Item 3 (Reversão de CSP relaxado): script-src nunca contém
    'unsafe-inline' — com ou sem nonce por requisição."""
    for headers in (
        SecurityService.get_security_headers(),
        SecurityService.get_security_headers(nonce="abc123"),
    ):
        d = _parse_csp(headers["Content-Security-Policy"])
        assert "script-src" in d
        assert "'unsafe-inline'" not in d["script-src"], (
            "VULNERABILIDADE: 'unsafe-inline' em script-src proíbe o CSP relaxado"
        )


def test_nonce_por_requisicao_aplicado_no_header():
    """CSP com nonce inclui 'nonce-<v>' em script-src; sem nonce, apenas a base."""
    sem_nonce = _parse_csp(SecurityService.get_security_headers()["Content-Security-Policy"])
    com_nonce = _parse_csp(SecurityService.get_security_headers(nonce="abc123")["Content-Security-Policy"])
    assert "nonce-" not in sem_nonce["script-src"]
    assert "'nonce-abc123'" in com_nonce["script-src"]


def test_script_src_attr_permite_handlers_inline():
    """Handlers inline (onclick/oninput/...) seguem permitidos via script-src-attr
    'unsafe-inline', mantendo script-src estrito (sem unsafe-inline)."""
    for headers in (
        SecurityService.get_security_headers(),
        SecurityService.get_security_headers(nonce="abc123"),
    ):
        d = _parse_csp(headers["Content-Security-Policy"])
        assert d.get("script-src-attr") == "'unsafe-inline'"


def test_new_nonce_genera_entropia_suficiente():
    """new_nonce() retorna base64url sem padding com 128 bits de entropia (16 bytes)."""
    n1 = SecurityService.new_nonce()
    n2 = SecurityService.new_nonce()
    assert len(n1) == 22
    assert n1 != n2
    assert "+" not in n1 and "/" not in n1 and "=" not in n1


def test_inject_nonce_substitui_placeholder():
    """inject_nonce() troca o placeholder __CSP_NONCE__ pelo nonce real do header."""
    html = '<script type="module" nonce="__CSP_NONCE__">import x from "https://cdn.jsdelivr.net/x";</script>'
    injetado = SecurityService.inject_nonce(html, "abc123")
    assert '__CSP_NONCE__' not in injetado
    assert 'nonce="abc123"' in injetado
    assert SecurityService.inject_nonce(html) == html, "sem nonce o HTML deve ficar intacto"


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
        p for p in [
            root / "templates" / "core" / "security.py",
            root / "templates" / "v2" / "security.py",
            root / "src" / "core" / "security.py",
        ] if p.exists()
    ]
    assert len(caminhos) >= 1, "Nenhum arquivo security.py encontrado"

    for p in caminhos:
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
