# -*- coding: utf-8 -*-
"""
Módulo de Handoff Estruturado e Assinatura HMAC para aidd-tdd (D15 / DoD 8).
Gera manifesto final com integridade criptográfica HMAC-SHA256 para transferir o bastão com segurança.
"""

from __future__ import annotations

import datetime
import hashlib
import hmac
import json
from pathlib import Path


def _calcular_hmac(dados_dict: dict, chave: str) -> str:
    conteudo_canonico = json.dumps(dados_dict, sort_keys=True, ensure_ascii=False)
    return hmac.new(
        chave.encode("utf-8"),
        conteudo_canonico.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()


def gerar_handoff(sessao_path: str | Path, output_path: str | Path, chave: str = "aidd-default-secret") -> bool:
    p = Path(sessao_path)
    if not p.exists():
        return False

    try:
        with open(p, "r", encoding="utf-8") as f:
            estado = json.load(f)

        payload = {
            "alvo": estado.get("alvo"),
            "seam": estado.get("seam"),
            "fase_final": estado.get("fase_atual"),
            "testes": estado.get("testes", []),
            "gerado_em": datetime.datetime.now().isoformat()
        }

        assinatura = _calcular_hmac(payload, chave)
        pacote = {
            "versao_handoff": "1.0",
            "ferramenta": "aidd-tdd",
            "assinatura_hmac_sha256": assinatura,
            "payload": payload
        }

        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(pacote, f, indent=2, ensure_ascii=False)

        return True
    except Exception:
        return False


def verificar_handoff(handoff_path: str | Path, chave: str = "aidd-default-secret") -> bool:
    p = Path(handoff_path)
    if not p.exists():
        return False

    try:
        with open(p, "r", encoding="utf-8") as f:
            pacote = json.load(f)

        payload = pacote.get("payload")
        assinatura_esperada = pacote.get("assinatura_hmac_sha256")

        if not payload or not assinatura_esperada:
            return False

        assinatura_calculada = _calcular_hmac(payload, chave)
        return hmac.compare_digest(assinatura_esperada, assinatura_calculada)
    except Exception:
        return False
