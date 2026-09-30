# -*- coding: utf-8 -*-
"""
Módulo de Observabilidade e Métricas de Especificação para aidd-spec (Ticket 6 / D12 / DoD 5).
Calcula métricas quantitativas de robustez: densidade de invariantes, critérios binários e contratos tipados.
"""

from __future__ import annotations

import datetime
import json
import time
from pathlib import Path
from typing import Dict, Any


class RastreadorSpec:
    """Calcula telemetria estrutural do documento de especificação técnica."""

    def __init__(self):
        self.inicio = time.time()
        self.metricas: Dict[str, Any] = {}

    def analisar_especificacao(self, secoes: Dict[str, str], resumo_motor: Dict[str, Any]) -> Dict[str, Any]:
        contratos_texto = secoes.get("contratos", "")
        linhas_contrato = [l for l in contratos_texto.splitlines() if l.strip().startswith("-") or "class " in l or "interface " in l or "type " in l]

        modos_falha_texto = secoes.get("modos_falha", "")
        linhas_falha = [l for l in modos_falha_texto.splitlines() if l.strip().startswith("-") or re_match_num(l)]

        self.metricas = {
            "total_invariantes": resumo_motor.get("total_invariantes", 0),
            "total_criterios_binarios": resumo_motor.get("total_criterios_binarios", 0),
            "interfaces_contratos_detectados": len(linhas_contrato),
            "modos_falha_mapeados": len(linhas_falha),
            "tempo_processamento_ms": round((time.time() - self.inicio) * 1000, 2),
            "gerado_em": datetime.datetime.now().isoformat()
        }
        return self.metricas

    def salvar_metricas(self, output_path: str | Path) -> None:
        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(self.metricas, f, indent=2, ensure_ascii=False)


def re_match_num(linha: str) -> bool:
    import re
    return bool(re.match(r"^\d+[\.\)]", linha.strip()))
