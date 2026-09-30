# -*- coding: utf-8 -*-
"""
Módulo de Observabilidade e Telemetria para aidd-tdd (D12 / DoD 5).
Rastreia tempos de execução por fase (Red, Green, Refactor) e métricas quantitativas de asserções.
"""

from __future__ import annotations

import datetime
import json
import time
from pathlib import Path
from typing import Dict, Any


class RastreadorTdd:
    """Monitora a telemetria do ciclo TDD e gera relatórios de métricas determinísticos."""

    def __init__(self, seam: str):
        self.seam = seam
        self.inicio_geral = time.time()
        self.tempos_inicio: Dict[str, float] = {}
        self.duracao_fases: Dict[str, float] = {}
        self.metricas_customizadas: Dict[str, Any] = {}

    def iniciar_fase(self, nome_fase: str) -> None:
        self.tempos_inicio[nome_fase] = time.time()

    def finalizar_fase(self, nome_fase: str) -> float:
        if nome_fase not in self.tempos_inicio:
            return 0.0
        duracao = time.time() - self.tempos_inicio[nome_fase]
        self.duracao_fases[nome_fase] = duracao
        return duracao

    def registrar_metrica(self, chave: str, valor: Any) -> None:
        self.metricas_customizadas[chave] = valor

    def consolidar(self) -> Dict[str, Any]:
        return {
            "seam": self.seam,
            "duracao_total_segundos": time.time() - self.inicio_geral,
            "duracao_fases": self.duracao_fases,
            "metricas_customizadas": self.metricas_customizadas,
            "gerado_em": datetime.datetime.now().isoformat()
        }

    def salvar_metricas(self, output_path: str | Path) -> None:
        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(self.consolidar(), f, indent=2, ensure_ascii=False)
