#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
QUALITY GATE: G_BRIDGE_VENDOR_LOCKIN
===============================================================================
Valida que o projeto extraído/empacotado pela aidd-bridge não possui
dependências ou URLs fixas de nuvens proprietárias (ex: *.supabase.co,
mock backends não configuráveis). Garante independência total.

Exit 0: Sem vendor lock-in detectado.
Exit 1: URLs proprietárias hardcoded ou travas de nuvem encontradas.
===============================================================================
"""

import os
import sys
import re

PATTERNS_PROIBIDOS = [
    (re.compile(r"https?://[a-zA-Z0-9_\-]+\.supabase\.co(?!\w)", re.IGNORECASE), "URL hardcoded do Supabase Cloud encontrada"),
    (re.compile(r"https?://[a-zA-Z0-9_\-]+\.firebaseio\.com", re.IGNORECASE), "URL hardcoded do Firebase Cloud encontrada"),
]

EXTENSOES_VARREDURA = {".ts", ".tsx", ".js", ".jsx", ".json", ".sql", ".env"}


def audit_vendor_lockin(target_dir: str) -> int:
    erros = []
    total_arquivos = 0

    for root, dirs, files in os.walk(target_dir):
        # Ignora pastas de build, dependencias e git
        dirs[:] = [d for d in dirs if d not in {"node_modules", "dist", ".git", ".next", ".nuxt", "__pycache__"}]
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in EXTENSOES_VARREDURA:
                total_arquivos += 1
                caminho = os.path.join(root, f)
                try:
                    with open(caminho, "r", encoding="utf-8", errors="ignore") as fp:
                        conteudo = fp.read()
                        for regex, msg in PATTERNS_PROIBIDOS:
                            if regex.search(conteudo):
                                rel = os.path.relpath(caminho, target_dir)
                                erros.append(f"  [BLOQUEIO] {rel}: {msg}")
                except Exception as exc:
                    pass

    print("=" * 72)
    print(" [GATE] G_BRIDGE_VENDOR_LOCKIN — Auditoria de Desacoplamento de Nuvem")
    print("=" * 72)
    print(f"  Diretório auditado : {target_dir}")
    print(f"  Arquivos analisados: {total_arquivos}")

    if erros:
        print(f"\n [FALHA] Foram encontrados indícios de Vendor Lock-in ({len(erros)} ocorrência(s)):")
        for err in erros:
            print(err)
        print("\n Solução: Substitua URLs e chaves proprietárias por variáveis de ambiente (ex: VITE_SUPABASE_URL).")
        print("=" * 72)
        return 1

    print(" [SUCESSO] Zero Vendor Lock-in detectado. O código está 100% livre e portável.")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    caminho = sys.argv[1] if len(sys.argv) > 1 else "."
    sys.exit(audit_vendor_lockin(os.path.abspath(caminho)))
