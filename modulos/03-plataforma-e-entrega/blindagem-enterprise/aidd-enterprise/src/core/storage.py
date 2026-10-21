# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — OBJECT STORAGE CLIENT (Cloudflare R2 / S3-Compatible)
=============================================================================
Cliente de armazenamento de objetos compatível com API S3v4 e taxa zero
de saída (Cloudflare R2).
Regido pelas 9 Camadas de Mercado de CONSTRAINTS.md (Camada 6 — RevNault):
  - Geração de Presigned URLs temporárias (PUT/GET).
  - Whitelist estrita de MIME types permitidos e bloqueio de executáveis.
  - Particionamento multi-tenant seguro ({tenant_id}/{modulo}/... - Anti-IDOR).
=============================================================================
"""

import os
import uuid
import datetime
from typing import Any, Dict, List, Optional, Tuple

try:
    import boto3
    from botocore.config import Config
    from botocore.exceptions import ClientError
except ImportError:
    boto3 = None
    Config = None
    ClientError = Exception


EXTENSOES_PROIBIDAS = {
    ".exe", ".bat", ".cmd", ".sh", ".bash", ".ps1", ".vbs",
    ".py", ".pyc", ".pyd", ".dll", ".so", ".dylib", ".bin",
    ".msi", ".jar", ".com", ".scr", ".pif", ".elf"
}

ALLOWED_MIME_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/svg+xml": ".svg",
    "application/pdf": ".pdf",
    "text/plain": ".txt",
    "text/csv": ".csv",
    "application/json": ".json",
    "audio/webm": ".webm",
    "video/webm": ".webm",
    "application/octet-stream": ".stl",  # Malhas 3D
    "application/dicom": ".dcm",         # Tomografias / Imagens Médicas
}


class R2StorageClient:
    """Cliente gerenciado de Cloudflare R2 / S3v4 com governança de segurança."""

    def __init__(
        self,
        endpoint_url: Optional[str] = None,
        access_key_id: Optional[str] = None,
        secret_access_key: Optional[str] = None,
        bucket_name: Optional[str] = None,
        region_name: str = "auto"
    ):
        self.endpoint_url = endpoint_url or os.environ.get("R2_ENDPOINT_URL", "https://mock.r2.cloudflarestorage.com")
        self.access_key_id = access_key_id or os.environ.get("R2_ACCESS_KEY_ID", "mock_key")
        self.secret_access_key = secret_access_key or os.environ.get("R2_SECRET_ACCESS_KEY", "mock_secret")
        self.bucket_name = bucket_name or os.environ.get("R2_BUCKET_NAME", "aidd-storage")
        self.region_name = region_name

        self._s3_client = None
        if boto3 is not None and "mock" not in self.endpoint_url:
            self._s3_client = boto3.client(
                "s3",
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key,
                region_name=self.region_name,
                config=Config(signature_version="s3v4")
            )

    def validar_arquivo(self, nome_arquivo: str, mime_type: str) -> Tuple[bool, Optional[str]]:
        """Valida se a extensão e o MIME type são aceitos pelas diretrizes de segurança."""
        _, ext = os.path.splitext(nome_arquivo.lower())
        if ext in EXTENSOES_PROIBIDAS:
            return False, f"Extensão de arquivo proibida por política de segurança: {ext}"

        if mime_type.lower() not in ALLOWED_MIME_TYPES:
            return False, f"MIME type não autorizado: {mime_type}"

        return True, None

    def construir_chave_objeto(self, tenant_id: str, modulo: str, nome_arquivo: str) -> str:
        """Gera chave particionada por tenant: {tenant_id}/{modulo}/{yyyy}/{mm}/{uuid}.{ext}."""
        agora = datetime.datetime.now(datetime.timezone.utc)
        ano = agora.strftime("%Y")
        mes = agora.strftime("%m")
        _, ext = os.path.splitext(nome_arquivo.lower())
        unique_id = str(uuid.uuid4())
        tenant_limpo = str(tenant_id).strip().replace("/", "_")
        modulo_limpo = str(modulo).strip().replace("/", "_")
        return f"{tenant_limpo}/{modulo_limpo}/{ano}/{mes}/{unique_id}{ext}"

    def gerar_url_upload(
        self,
        tenant_id: str,
        modulo: str,
        nome_arquivo: str,
        mime_type: str,
        expiracao_segundos: int = 3600
    ) -> Dict[str, Any]:
        """Gera URL pré-assinada temporária para upload direto do cliente (S3v4 PUT)."""
        valido, motivo = self.validar_arquivo(nome_arquivo, mime_type)
        if not valido:
            return {"sucesso": False, "erro": motivo}

        object_key = self.construir_chave_objeto(tenant_id, modulo, nome_arquivo)

        if self._s3_client is not None:
            try:
                url = self._s3_client.generate_presigned_url(
                    ClientMethod="put_object",
                    Params={
                        "Bucket": self.bucket_name,
                        "Key": object_key,
                        "ContentType": mime_type
                    },
                    ExpiresIn=expiracao_segundos
                )
                return {
                    "sucesso": True,
                    "upload_url": url,
                    "object_key": object_key,
                    "expira_em_segundos": expiracao_segundos
                }
            except ClientError as e:
                return {"sucesso": False, "erro": str(e)}

        # Modo simulado determinístico para dev/testes locais sem credenciais de nuvem
        simulated_url = f"{self.endpoint_url}/{self.bucket_name}/{object_key}?X-Amz-Signature=mock_signature&expires={expiracao_segundos}"
        return {
            "sucesso": True,
            "upload_url": simulated_url,
            "object_key": object_key,
            "expira_em_segundos": expiracao_segundos
        }

    def gerar_url_download(
        self,
        object_key: str,
        tenant_id_solicitante: str,
        expiracao_segundos: int = 3600
    ) -> Dict[str, Any]:
        """Gera URL de download com validação Anti-IDOR verificando o prefixo do tenant."""
        # Proteção estrita Anti-IDOR: o tenant só pode baixar seus próprios objetos
        tenant_prefix = f"{tenant_id_solicitante.strip()}/"
        if not object_key.startswith(tenant_prefix):
            return {
                "sucesso": False,
                "erro": "Violação de isolamento multi-tenant (Anti-IDOR): acesso negado ao objeto de outro tenant."
            }

        if self._s3_client is not None:
            try:
                url = self._s3_client.generate_presigned_url(
                    ClientMethod="get_object",
                    Params={
                        "Bucket": self.bucket_name,
                        "Key": object_key
                    },
                    ExpiresIn=expiracao_segundos
                )
                return {
                    "sucesso": True,
                    "download_url": url,
                    "expira_em_segundos": expiracao_segundos
                }
            except ClientError as e:
                return {"sucesso": False, "erro": str(e)}

        simulated_url = f"{self.endpoint_url}/{self.bucket_name}/{object_key}?X-Amz-Signature=mock_download_sig"
        return {
            "sucesso": True,
            "download_url": simulated_url,
            "expira_em_segundos": expiracao_segundos
        }
