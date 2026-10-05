# -*- coding: utf-8 -*-
"""
Observabilidade, Métricas e Orçamento de Tokens (VSA).
Dimensão D12: Observabilidade e Frugalidade.
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional


class GravadorTelemetriaVSA:
    def __init__(self, arquivo_saida: Path):
        self.arquivo_saida = Path(arquivo_saida)
        self.inicio_tempo: Optional[float] = None
        self.slices_registrados: List[Dict[str, int]] = []
        self._iniciado = False

    def iniciar(self) -> None:
        self.inicio_tempo = time.time()
        self.slices_registrados = []
        self._iniciado = True

    def registrar_slice(self, nome_slice: str, tokens: int) -> None:
        if not self._iniciado:
            raise RuntimeError("Telemetria não iniciada. Chame iniciar() primeiro.")
        self.slices_registrados.append({
            "slice": nome_slice,
            "tokens": tokens
        })

    def finalizar(self) -> Dict[str, any]:
        if not self._iniciado:
            raise RuntimeError("Telemetria não iniciada.")
        duracao = round(time.time() - (self.inicio_tempo or time.time()), 4)
        total_tokens = sum(s["tokens"] for s in self.slices_registrados)

        relatorio = {
            "status": "concluido",
            "duracao_segundos": duracao,
            "total_slices_verificados": len(self.slices_registrados),
            "orcamento_tokens_consumido": total_tokens,
            "slices": self.slices_registrados
        }

        self.arquivo_saida.parent.mkdir(parents=True, exist_ok=True)
        self.arquivo_saida.write_text(json.dumps(relatorio, indent=2, ensure_ascii=False), encoding="utf-8")
        self._iniciado = False
        return relatorio
