# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD-Ops MVP — Fase 3: Sizing e Síntese Dinâmica da Camada de Dados
=============================================================================
Soma os requisitos de vCPU/RAM/disco de cada ferramenta a partir de
data/requisitos_recursos.json, retorna spec de VPS (totais arredondados
para cima) + lista de bancos lógicos necessários (uma entrada por
ferramenta que necessitar de banco relacional).

100% determinístico — zero LLM, aritmética pura.
"""

from __future__ import annotations

import json
import math
import os
import sys
from typing import Any, Dict, List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
from core.result import Result

_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")


def _carregar_requisitos() -> Dict[str, Any]:
    caminho = os.path.join(_DATA_DIR, "requisitos_recursos.json")
    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)


def dimensionar(ferramentas: List[Dict[str, str]]) -> Result:
    """Dimensiona os recursos de VPS e lista bancos lógicos necessários.

    Args:
        ferramentas: Lista de dicts com chave "nome" (ex: [{"nome": "Typebot"}, ...]).

    Returns:
        Result.ok(dados_sizing) com vps, bancos_logicos, fontes_consultadas.
    """
    if not ferramentas:
        return Result.fail(
            "Lista de ferramentas vazia — nada a dimensionar.",
            codigo="FERRAMENTAS_VAZIAS",
        )

    requisitos_data = _carregar_requisitos()
    ferramentas_req = requisitos_data.get("ferramentas", {})

    total_vcpu = 0.0
    total_ram = 0.0
    total_disco = 0.0
    bancos_logicos: List[Dict[str, str]] = []
    ferramentas_com_banco: List[str] = []
    ferramentas_sem_banco: List[str] = []
    fontes_consultadas: List[Dict[str, Any]] = []
    ferramentas_nao_encontradas: List[str] = []

    for ferramenta in ferramentas:
        nome = ferramenta["nome"]
        req = ferramentas_req.get(nome)

        if req is None:
            ferramentas_nao_encontradas.append(nome)
            # Ferramenta não encontrada: não somar nada, registrar
            fontes_consultadas.append({
                "ferramenta": nome,
                "url": "",
                "requisitos_encontrados": False,
                "notas": "Ferramenta não encontrada no catálogo de requisitos.",
            })
            ferramentas_sem_banco.append(nome)
            continue

        total_vcpu += req.get("vcpu", 1)
        total_ram += req.get("ram_gb", 1)
        total_disco += req.get("disco_gb", 20)

        # Banco relacional
        if req.get("requer_banco_relacional", False):
            ferramentas_com_banco.append(nome)
            nome_banco_slug = nome.lower().replace(" ", "_").replace(".", "")
            bancos_logicos.append({
                "ferramenta": nome,
                "nome_banco": f"{nome_banco_slug}_db",
            })
        else:
            ferramentas_sem_banco.append(nome)

        # Fonte consultada
        fontes_consultadas.append({
            "ferramenta": nome,
            "url": req.get("fonte", ""),
            "requisitos_encontrados": req.get("requisitos_oficiais", False),
            "notas": req.get("notas", ""),
        })

    if ferramentas_nao_encontradas:
        # Não é erro fatal — ferramentas desconhecidas são ignoradas no sizing,
        # mas o relatório final deve mencioná-las
        for nome in ferramentas_nao_encontradas:
            fontes_consultadas.append({
                "ferramenta": nome,
                "url": "",
                "requisitos_encontrados": False,
                "notas": "Ferramenta não encontrada no catálogo de requisitos — "
                         "recursos não incluídos no dimensionamento.",
            })

    # Arredondar para cima com margem de 20% e mínimo prático
    margem = 1.2
    vcpu_final = max(2, math.ceil(total_vcpu * margem))
    ram_final = max(4, math.ceil(total_ram * margem))
    disco_final = max(40, math.ceil(total_disco * margem))

    resultado = {
        "vps": {
            "vcpu": vcpu_final,
            "ram_gb": ram_final,
            "disco_gb": disco_final,
        },
        "bancos_logicos": bancos_logicos,
        "ferramentas_com_banco": ferramentas_com_banco,
        "ferramentas_sem_banco": ferramentas_sem_banco,
        "fontes_consultadas": fontes_consultadas,
    }

    return Result.ok(resultado)
