# -*- coding: utf-8 -*-
"""
Assinatura criptográfica HMAC-SHA256 e validação de integridade para aidd-handoff (D15).
"""

from __future__ import annotations

import hashlib
import hmac
import json
from pathlib import Path
from typing import Dict, Any


def _computar_hmac(dados: Dict[str, Any], secret: str) -> str:
    # Remove a chave de assinatura se presente antes de calcular
    copia = {k: v for k, v in dados.items() if k != "assinatura_hmac"}
    payload_str = json.dumps(copia, sort_keys=True, ensure_ascii=False)
    return hmac.new(secret.encode("utf-8"), payload_str.encode("utf-8"), hashlib.sha256).hexdigest()


def emitir_manifesto(caminho_arquivo: str | Path, secret: str = "aidd-default-secret") -> Dict[str, Any]:
    p = Path(caminho_arquivo).resolve()
    conteudo = p.read_bytes() if p.exists() else b""
    hash_conteudo = hashlib.sha256(conteudo).hexdigest()

    manifesto: Dict[str, Any] = {
        "tipo": "aidd-handoff",
        "versao": "1.0",
        "arquivo": str(p),
        "hash_sha256": hash_conteudo,
    }
    manifesto["assinatura_hmac"] = _computar_hmac(manifesto, secret)
    return manifesto


def verificar_manifesto(manifesto: Dict[str, Any], secret: str = "aidd-default-secret") -> bool:
    if "assinatura_hmac" not in manifesto:
        return False
    assinatura_esperada = _computar_hmac(manifesto, secret)
    return hmac.compare_digest(manifesto["assinatura_hmac"], assinatura_esperada)
