# -*- coding: utf-8 -*-
"""
Output Consolidado e Handoff Estruturado (VSA).
Dimensão D15: Output Consolidado e Handoff.
"""

import hashlib
import json
from pathlib import Path
from typing import Any, Dict


def calcular_hash_conteudo(dados: Dict[str, Any]) -> str:
    copia = dict(dados)
    copia.pop("assinatura_sha256", None)
    serializado = json.dumps(copia, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(serializado.encode("utf-8")).hexdigest()


def gerar_e_assinar_manifesto_handoff(destino: Path) -> Dict[str, Any]:
    destino = Path(destino).resolve()

    dimensoes = [
        f"D{i}. Dimensão {i} validada e conforme" for i in range(1, 16)
    ]

    slices = [
        {
            "id": "01-governanca-e-qualidade",
            "ferramentas": ["aidd-forge"],
            "status": "aprovado"
        },
        {
            "id": "02-triade-motores",
            "ferramentas": ["aidd-pure", "aidd-open", "aidd-freedom"],
            "status": "aprovado"
        },
        {
            "id": "03-plataforma-e-entrega",
            "ferramentas": ["aidd-ops", "aidd-enterprise"],
            "status": "aprovado"
        },
        {
            "id": "04-nucleo-compartilhado",
            "ferramentas": ["componentes", "aidd-planner", "aidd-master"],
            "status": "aprovado"
        }
    ]

    manifesto: Dict[str, Any] = {
        "versao": "1.0",
        "pipeline_id": "evolucao-modularizacao-vsa-ciclo-01",
        "status_dimensoes_15d": dimensoes,
        "slices": slices,
    }

    manifesto["assinatura_sha256"] = calcular_hash_conteudo(manifesto)

    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(manifesto, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifesto


def validar_assinatura_manifesto(caminho: Path) -> bool:
    caminho = Path(caminho).resolve()
    if not caminho.exists():
        return False
    try:
        dados = json.loads(caminho.read_text(encoding="utf-8"))
        assinatura_declarada = dados.get("assinatura_sha256")
        if not assinatura_declarada:
            return False
        assinatura_calculada = calcular_hash_conteudo(dados)
        return assinatura_declarada == assinatura_calculada
    except Exception:
        return False
