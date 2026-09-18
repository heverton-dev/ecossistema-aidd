# -*- coding: utf-8 -*-
"""Use Case: attach-vsa — conecta um backend VSA (core kernel + modulo +
server.py + Quarteto Sine Qua Non) a um projeto cujo frontend ja existe e
deve ser preservado (ex: saida do aidd-bridge, FLUXO 03). Nunca gera nem
sobrescreve Dockerfile/docker-compose.yml/nginx/frontend do frontend
preservado -- so acrescenta o backend por cima."""

import os
import sys


def cmd_attach_vsa(args):
    scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "scripts")
    sys.path.insert(0, scripts_dir)
    from provision_project import provision_backend_only
    from attach_vsa_infra import attach_infra

    project_dir = os.path.abspath(getattr(args, "dir", "."))
    resultado = provision_backend_only(project_dir, args.nome, getattr(args, "descricao", "") or "")

    infra = attach_infra(project_dir)
    if infra["conectado"]:
        print(f"[+] Backend VSA conectado ao Dockerfile/Caddyfile ja existentes:")
        print(f"    - {infra['dockerfile_api']}")
        print(f"    - {infra['compose']} (servico 'api' adicionado)")
        print(f"    - {infra['caddyfile']} (rotas /docs, /webhooks, /mcp, /metrics roteadas para 'api')")
    else:
        print(f"[i] {infra['motivo']} -- backend gerado, mas infra Docker/Caddy nao foi mesclada.")

    return resultado
