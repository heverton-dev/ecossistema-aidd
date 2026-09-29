# -*- coding: utf-8 -*-
"""
Bite tests (Lei #13 — Todo Portão Deve Provar Que Morde) para os 4
Quality Gates da aidd-bridge. Cada teste injeta uma violação deliberada
e asserta exit 1 (reprovação real), não caminho feliz.
"""

import json
import os
import sys
import tempfile

BRIDGE_DIR = os.path.dirname(os.path.dirname(__file__))
GATES_DIR = os.path.join(BRIDGE_DIR, "gates")
sys.path.insert(0, BRIDGE_DIR)
sys.path.insert(0, GATES_DIR)

from G_BRIDGE_VENDOR_LOCKIN import audit_vendor_lockin
from G_BRIDGE_DOCKER_OCI import audit_docker_oci
from G_BRIDGE_POSTGRESQL import audit_postgresql_script
from G_BRIDGE_VSA_COMPAT import audit_vsa_compat


def test_bite_vendor_lockin_url_supabase_cloud_em_tsx():
    """Violação deliberada: URL hardcoded do Supabase Cloud em .tsx."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "App.tsx"), "w", encoding="utf-8") as f:
            f.write("const url = 'https://projeto.supabase.co';\n")
        assert audit_vendor_lockin(tmpdir) == 1


def test_bite_docker_oci_user_root_no_dockerfile():
    """Violação deliberada: Dockerfile multi-stage que sobe como root."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "Dockerfile"), "w", encoding="utf-8") as f:
            f.write(
                "FROM node:20-alpine AS builder\n"
                "WORKDIR /app\n"
                "FROM nginx:alpine\n"
                "USER root\n"
            )
        with open(os.path.join(tmpdir, "nginx.conf"), "w", encoding="utf-8") as f:
            f.write(
                "server { listen 80; add_header X-Content-Type-Options nosniff;"
                " add_header X-Frame-Options DENY; }\n"
            )
        assert audit_docker_oci(tmpdir) == 1


def test_bite_postgresql_extensao_proibida_pg_cron():
    """Violação deliberada: init-db.sql com extensão não portável (pg_cron)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "init-db.sql"), "w", encoding="utf-8") as f:
            f.write(
                "CREATE EXTENSION IF NOT EXISTS pg_cron;\n"
                "CREATE TABLE items (id SERIAL PRIMARY KEY);\n"
            )
        assert audit_postgresql_script(tmpdir) == 1


def test_bite_vsa_compat_quarteto_sem_swagger():
    """Violação deliberada: quarteto_sine_qua_non/ sem swagger_spec.json."""
    with tempfile.TemporaryDirectory() as tmpdir:
        quarteto = os.path.join(tmpdir, "quarteto_sine_qua_non")
        os.makedirs(quarteto)
        with open(os.path.join(quarteto, "webhooks_contract.json"), "w", encoding="utf-8") as f:
            json.dump({"algorithm": "HMAC-SHA256"}, f)
        with open(os.path.join(quarteto, "mcp_studio.json"), "w", encoding="utf-8") as f:
            json.dump({"tools": []}, f)
        with open(os.path.join(quarteto, "USER_GUIDE.md"), "w", encoding="utf-8") as f:
            f.write("# Guia\n")
        # swagger_spec.json ausente de propósito
        assert audit_vsa_compat(tmpdir) == 1
