# -*- coding: utf-8 -*-
"""
Validador de Integridade Criptográfica (SHA-256) de Contratos de Handoff.

Garante que artefatos JSON compartilhados entre etapas (PLANNER, vsa_dispatch,
handoff_evolution) não foram adulterados ou corrompidos durante o pipeline.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Tuple


def calcular_sha256_payload(dados: Dict[str, Any]) -> str:
    """Calcula o hash SHA-256 de um payload JSON canonicalizado.

    Exclui campos voláteis como 'payload_sha256' para auto-consistência.
    """
    copia = {k: v for k, v in dados.items() if k != "payload_sha256"}
    canonico = json.dumps(
        copia,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(canonico).hexdigest()


def assinar_contrato_payload(dados: Dict[str, Any]) -> Dict[str, Any]:
    """Calcula o SHA-256 do payload e insere no campo 'payload_sha256'."""
    sha = calcular_sha256_payload(dados)
    novo = dict(dados)
    novo["payload_sha256"] = sha
    return novo


def validar_integridade_contrato(caminho_ou_dados: Path | str | Dict[str, Any]) -> Tuple[bool, str]:
    """Valida a integridade SHA-256 de um contrato JSON.

    Retorna (True, "") se válido, ou (False, motivo) se corrompido ou ausente.
    """
    if isinstance(caminho_ou_dados, (Path, str)):
        p = Path(caminho_ou_dados)
        if not p.is_file():
            return False, f"Arquivo de contrato não encontrado: {p}"
        try:
            with open(p, "r", encoding="utf-8") as f:
                dados = json.load(f)
        except Exception as e:
            return False, f"JSON malformado em {p}: {e}"
    elif isinstance(caminho_ou_dados, dict):
        dados = caminho_ou_dados
    else:
        return False, "Tipo inválido para verificação de integridade"

    hash_declarado = dados.get("payload_sha256")
    if not hash_declarado:
        return False, "Campo obrigatório 'payload_sha256' ausente no contrato"

    if not isinstance(hash_declarado, str) or len(hash_declarado) != 64:
        return False, f"Hash SHA-256 inválido (esperado hex de 64 caracteres): '{hash_declarado}'"

    hash_calculado = calcular_sha256_payload(dados)
    if hash_declarado.lower() != hash_calculado.lower():
        return False, (
            f"Violação de integridade SHA-256: esperado '{hash_declarado}', "
            f"calculado '{hash_calculado}'"
        )

    return True, ""
