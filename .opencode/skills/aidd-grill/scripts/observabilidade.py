# -*- coding: utf-8 -*-
"""
Módulo de Observabilidade e Métricas de Entrevista Socrática para aidd-grill (Ticket 6 / D12 / DoD 5).
Calcula métricas quantitativas de perguntas formuladas, opções e premissas consolidadas.
"""

from __future__ import annotations

import datetime
import json
import time
from pathlib import Path
from typing import Dict, Any, List


class RastreadorGrill:
    """Calcula telemetria estrutural das rodadas de entrevista socrática."""

    def __init__(self):
        self.inicio = time.time()
        self.metricas: Dict[str, Any] = {}

    def analisar_rodada(self, perguntas: List[Dict[str, Any]], resumo_motor: Dict[str, Any]) -> Dict[str, Any]:
        total_opcoes = sum(len(p.get("opcoes", [])) for p in perguntas)

        self.metricas = {
            "total_perguntas": len(perguntas),
            "total_opcoes_mapeadas": total_opcoes,
            "perguntas_com_recomendacao_justificada": resumo_motor.get("total_validadas", 0),
            "premissas_consolidadas": len(resumo_motor.get("premissas_consolidadas", [])),
            "tempo_processamento_ms": round((time.time() - self.inicio) * 1000, 2),
            "gerado_em": datetime.datetime.now().isoformat()
        }
        return self.metricas

    def salvar_metricas(self, output_path: str | Path) -> None:
        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(self.metricas, f, indent=2, ensure_ascii=False)
