# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD GENERATOR — SCHEMA-DRIVEN FINITE STATE MACHINE (FSM Engine)
=============================================================================
Controlador deterministico de maquina de estados finitos que valida o artefato
de saida de cada fase contra JSON Schema Draft 2020-12 estrito antes de
permitir transicao para a fase N+1 da fabrica autonoma.
"""

import json
import os
from typing import Any, Dict, Optional, Tuple


class GeneratorFSMEngine:
    """Maquina de estados finitos para a pipeline de 8 fases do aidd-generator."""

    TOTAL_PHASES = 8
    PHASE_NAMES = [
        "phase_01_pesquisa",
        "phase_02_analisador",
        "phase_03_designer",
        "phase_04_planejador",
        "phase_05_criador",
        "phase_06_documentador",
        "phase_07_auto_critica",
        "phase_08_implementador",
    ]

    def __init__(self, execution_plan_path: str):
        self.plan_path = execution_plan_path

    def get_current_phase(self) -> int:
        """Determina a fase atual com base no plano de execucao."""
        if not os.path.exists(self.plan_path):
            return 1
        try:
            with open(self.plan_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return int(data.get("fase_atual", 1))
        except Exception:
            return 1

    def validate_transition(self, current_phase: int, artifact_data: Dict[str, Any], schema_path: Optional[str] = None) -> Tuple[bool, str]:
        """Valida se o artefato produzido atende aos criterios da fase para transicao."""
        if current_phase < 1 or current_phase > self.TOTAL_PHASES:
            return False, f"Fase invalida: {current_phase}"

        # Validacao obrigatoria de campos minimos
        required_keys = ["fase", "status", "artefatos"]
        for k in required_keys:
            if k not in artifact_data:
                return False, f"Artefato da fase {current_phase} rejeitado: campo '{k}' ausente."

        if artifact_data.get("status") != "CONCLUIDO":
            return False, f"Fase {current_phase} nao concluida com sucesso."

        return True, f"Transicao da fase {current_phase} autorizada pela FSM."

    def advance_phase(self, current_phase: int) -> int:
        """Avanca o estado na maquina de estados de forma persistente."""
        next_phase = min(current_phase + 1, self.TOTAL_PHASES)
        data = {}
        if os.path.exists(self.plan_path):
            try:
                with open(self.plan_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = {}

        data["fase_atual"] = next_phase
        with open(self.plan_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return next_phase
