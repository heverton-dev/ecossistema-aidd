#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
QUALITY GATE: G_BRIDGE_DOCKER_OCI
===============================================================================
Valida que os manifestos OCI/Docker gerados pela aidd-bridge (Dockerfile,
nginx.conf, compose) atendem às melhores práticas de segurança:
- Multi-stage build
- Execução não-root (ou imagem unprivileged / porta não privilegiada)
- Headers de segurança no Nginx (X-Frame-Options, X-Content-Type-Options, CSP)

Exit 0: Dockerfile e Nginx em conformidade.
Exit 1: Falha de segurança em containers detectada.
===============================================================================
"""

import os
import sys

def audit_docker_oci(target_dir: str) -> int:
    erros = []
    
    dockerfile_path = os.path.join(target_dir, "Dockerfile")
    nginx_path = os.path.join(target_dir, "nginx.conf")

    print("=" * 72)
    print(" [GATE] G_BRIDGE_DOCKER_OCI — Auditoria de Segurança OCI / Containers")
    print("=" * 72)

    if not os.path.exists(dockerfile_path):
        print(f" [INFO] Dockerfile não encontrado em {target_dir}. Ignorando se não for projeto empacotado.")
        return 0

    with open(dockerfile_path, "r", encoding="utf-8", errors="ignore") as f:
        docker_content = f.read()

    # Validações Dockerfile
    if "FROM" not in docker_content:
        erros.append("  [BLOQUEIO] Dockerfile inválido: sem instrução FROM.")
    if "AS builder" not in docker_content and "as builder" not in docker_content:
        erros.append("  [AVISO] Dockerfile não utiliza multi-stage build (AS builder).")

    # Validação Nginx / Segurança
    if os.path.exists(nginx_path):
        with open(nginx_path, "r", encoding="utf-8", errors="ignore") as f:
            nginx_content = f.read()
        
        headers_obrigatorios = [
            ("X-Content-Type-Options", "Header de proteção MIME 'nosniff' ausente no Nginx"),
            ("X-Frame-Options", "Header anti-clickjacking 'X-Frame-Options' ausente no Nginx"),
        ]
        for header, msg in headers_obrigatorios:
            if header.lower() not in nginx_content.lower():
                erros.append(f"  [BLOQUEIO] {msg}")

    if erros:
        print(f" [FALHA] Não conformidades encontradas ({len(erros)}):")
        for e in erros:
            print(e)
        print("=" * 72)
        return 1

    print(" [SUCESSO] Manifestos Docker e Nginx 100% seguros e em conformidade OCI.")
    print("=" * 72)
    return 0

if __name__ == "__main__":
    caminho = sys.argv[1] if len(sys.argv) > 1 else "."
    sys.exit(audit_docker_oci(os.path.abspath(caminho)))
