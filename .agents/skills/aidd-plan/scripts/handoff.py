# -*- coding: utf-8 -*-
"""
Output consolidado e assinatura HMAC-SHA256 para aidd-plan (D15).
"""

from __future__ import annotations

import hashlib
import hmac
import json
from pathlib import Path
from typing import Dict, Any


def _computar_hmac(dados: Dict[str, Any], secret: str) -> str:
    copia = {k: v for k, v in dados.items() if k != "assinatura_hmac"}
    payload_str = json.dumps(copia, sort_keys=True, ensure_ascii=False)
    return hmac.new(secret.encode("utf-8"), payload_str.encode("utf-8"), hashlib.sha256).hexdigest()


def emitir_manifesto(caminho_pasta: str | Path, secret: str = "aidd-default-secret") -> Dict[str, Any]:
    p = Path(caminho_pasta).resolve()
    arquivos = sorted(p.glob("*.md")) if p.exists() and p.is_dir() else []

    hasher = hashlib.sha256()
    for arq in arquivos:
        hasher.update(arq.name.encode("utf-8"))
        hasher.update(arq.read_bytes())

    manifesto: Dict[str, Any] = {
        "tipo": "aidd-plan",
        "versao": "1.0",
        "pasta": str(p),
        "total_arquivos": len(arquivos),
        "hash_sha256": hasher.hexdigest(),
    }
    manifesto["assinatura_hmac"] = _computar_hmac(manifesto, secret)
    return manifesto


def verificar_manifesto(manifesto: Dict[str, Any], secret: str = "aidd-default-secret") -> bool:
    if "assinatura_hmac" not in manifesto:
        return False
    assinatura_esperada = _computar_hmac(manifesto, secret)
    return hmac.compare_digest(manifesto["assinatura_hmac"], assinatura_esperada)
