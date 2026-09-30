# -*- coding: utf-8 -*-
"""
Módulo de Observabilidade e Métricas de Decomposição para aidd-tickets (Ticket 6 / D12 / DoD 5).
Calcula métricas estruturais do plano de tickets: paralelismo, profundidade do DAG e impacto em arquivos.
"""

from __future__ import annotations

import datetime
import json
import time
from pathlib import Path
from typing import List, Dict, Any


class RastreadorTickets:
    """Calcula telemetria estrutural do conjunto de tickets decompostos."""

    def __init__(self):
        self.inicio = time.time()
        self.metricas: Dict[str, Any] = {}

    def analisar_tickets(self, tickets: List[Dict[str, Any]]) -> Dict[str, Any]:
        arquivos = set()
        paralelos_iniciais = 0
        adjacencias = {}
        bloqueadores_map = {}

        for t in tickets:
            tid = t["id"]
            for f in t.get("target_files", []):
                arquivos.add(f)
            blockers = t.get("blocked_by", [])
            bloqueadores_map[tid] = blockers
            if not blockers:
                paralelos_iniciais += 1

        # Calcula profundidade máxima simples do DAG
        def calcular_profundidade(node: str, visitados: set) -> int:
            if node in visitados:
                return 1
            visitados.add(node)
            blockers = bloqueadores_map.get(node, [])
            if not blockers:
                return 1
            return 1 + max(calcular_profundidade(b, visitados.copy()) for b in blockers)

        profundidade_max = 1
        if tickets:
            profundidade_max = max(calcular_profundidade(t["id"], set()) for t in tickets)

        self.metricas = {
            "total_tickets": len(tickets),
            "total_arquivos_distintos": len(arquivos),
            "tickets_paralelos_iniciais": paralelos_iniciais,
            "profundidade_maxima_dag": profundidade_max,
            "tempo_processamento_ms": round((time.time() - self.inicio) * 1000, 2),
            "gerado_em": datetime.datetime.now().isoformat()
        }
        return self.metricas

    def salvar_metricas(self, output_path: str | Path) -> None:
        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(self.metricas, f, indent=2, ensure_ascii=False)
