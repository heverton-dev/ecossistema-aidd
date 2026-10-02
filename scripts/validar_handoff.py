# -*- coding: utf-8 -*-
"""
Validador de contratos de handoff entre etapas do pipeline.
"""
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List


def _calcular_sha256(caminho: Path) -> str:
    h = hashlib.sha256()
    try:
        with open(caminho, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
    except Exception:
        return ""
    return h.hexdigest()


def validar_handoff(handoff_path: str) -> bool:
    try:
        p = Path(handoff_path)
        if not p.exists():
            return False
        with open(p, "r", encoding="utf-8") as f:
            dados = json.load(f)

        # Requisitos mínimos do contrato
        servidor_sobe = dados.get("servidor_sobe")
        if servidor_sobe is not True:
            return False

        produzido_por = dados.get("produzido_por")
        projetado_por = dados.get("projetado_por")
        if not produzido_por or not isinstance(produzido_por, str):
            return False
        if not projetado_por or not isinstance(projetado_por, str):
            return False
        if produzido_por != projetado_por:
            return False

        slice_path = dados.get("slice_path")
        if not slice_path:
            return False
        if not Path(slice_path).exists():
            return False

        evidencias = dados.get("evidencias", [])
        if not isinstance(evidencias, list) or not evidencias:
            return False
        for ev in evidencias:
            caminho_ev = ev.get("caminho")
            if not caminho_ev:
                return False
            p_ev = Path(caminho_ev)
            if not p_ev.exists():
                return False
            sha_esperado = ev.get("sha256")
            if not sha_esperado:
                return False
            sha_calculado = _calcular_sha256(p_ev)
            if sha_calculado != sha_esperado:
                return False
            http_status = ev.get("http_status_medido")
            if http_status is None:
                return False
            if not isinstance(http_status, (int, float)):
                return False

        log_erros = dados.get("log_erros", [])
        if log_erros:
            return False

        return True
    except Exception:
        return False


def main():
    if len(sys.argv) < 2:
        print("Uso: validar_handoff.py <caminho_do_handoff.json>", file=sys.stderr)
        sys.exit(2)
    ok = validar_handoff(sys.argv[1])
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
