# -*- coding: utf-8 -*-
"""
Testes unitários do módulo de armazenamento Cloudflare R2 / S3v4 (R2StorageClient).
Valida segurança de upload, restrição de executáveis e proteção Anti-IDOR.
"""

import sys
import pytest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
SRC_CORE = ROOT_DIR / "componentes" / "compartilhado" / "src-core"
if str(SRC_CORE) not in sys.path:
    sys.path.insert(0, str(SRC_CORE))

from storage import R2StorageClient, EXTENSOES_PROIBIDAS


def test_validacao_seguranca_arquivos():
    client = R2StorageClient()

    # Rejeição de executáveis proibidos
    for ext in [".exe", ".sh", ".bat", ".py"]:
        valido, motivo = client.validar_arquivo(f"malware{ext}", "application/octet-stream")
        assert valido is False
        assert "proibida por política de segurança" in motivo

    # Rejeição de MIME types não autorizados
    valido_mime, motivo_mime = client.validar_arquivo("script.js", "application/javascript")
    assert valido_mime is False
    assert "MIME type não autorizado" in motivo_mime

    # Sucesso para arquivos permitidos (PDF, PNG, DICOM, STL)
    valido_ok, _ = client.validar_arquivo("laudo.pdf", "application/pdf")
    assert valido_ok is True

    valido_stl, _ = client.validar_arquivo("guia_cirurgica.stl", "application/octet-stream")
    assert valido_stl is True


def test_geracao_url_upload_particionamento():
    client = R2StorageClient()
    res = client.gerar_url_upload("clinica-xyz", "contratos", "proposta.pdf", "application/pdf")

    assert res["sucesso"] is True
    assert "upload_url" in res
    assert res["object_key"].startswith("clinica-xyz/contratos/")
    assert res["object_key"].endswith(".pdf")


def test_protecao_anti_idor_download():
    client = R2StorageClient()

    # Chave criada para o tenant clinica-alpha
    key_alpha = "clinica-alpha/laudos/2026/10/doc123.pdf"

    # Tentativa de acesso do próprio dono (sucesso)
    res_proprio = client.gerar_url_download(key_alpha, tenant_id_solicitante="clinica-alpha")
    assert res_proprio["sucesso"] is True
    assert "download_url" in res_proprio

    # Tentativa de acesso de outro tenant (bloqueio Anti-IDOR imediato)
    res_invasor = client.gerar_url_download(key_alpha, tenant_id_solicitante="clinica-beta")
    assert res_invasor["sucesso"] is False
    assert "Anti-IDOR" in res_invasor["erro"]
