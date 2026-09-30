# -*- coding: utf-8 -*-
"""
Módulo de Handoff Estruturado e Assinatura HMAC para aidd-spec (Ticket 8 / D15 / DoD 8).
Gera manifesto final com integridade criptográfica HMAC-SHA256 para transferir a especificação para /aidd-tickets ou /aidd-planner.
"""

from __future__ import annotations

import datetime
import hashlib
import hmac
import json
from pathlib import Path
from typing import Dict, Any


def _calcular_hmac(dados_dict: dict, chave: str) -> str:
    conteudo_canonico = json.dumps(dados_dict, sort_keys=True, ensure_ascii=False)
    return hmac.new(
        chave.encode("utf-8"),
        conteudo_canonico.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()


def gerar_handoff_spec(
    secoes: Dict[str, str],
    resumo_motor: Dict[str, Any],
    output_path: str | Path,
    chave: str = "aidd-spec-secret"
) -> bool:
    try:
        payload = {
            "total_invariantes": resumo_motor.get("total_invariantes", 0),
            "total_criterios_binarios": resumo_motor.get("total_criterios_binarios", 0),
            "invariantes": resumo_motor.get("invariantes", []),
            "criterios_binarios": resumo_motor.get("criterios_binarios", []),
            "secoes": list(secoes.keys()),
            "gerado_em": datetime.datetime.now().isoformat()
        }

        assinatura = _calcular_hmac(payload, chave)
        pacote = {
            "versao_handoff": "1.0",
            "ferramenta": "aidd-spec",
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


def verificar_handoff_spec(handoff_path: str | Path, chave: str = "aidd-spec-secret") -> bool:
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
