# -*- coding: utf-8 -*-
"""
Módulo de Limpeza e Rollback Seguro para aidd-tdd (D14 / DoD 7).
Permite reverter alterações e restaurar o estado da sessão para o último ponto GREEN conhecido.
"""

from __future__ import annotations

import datetime
import json
from pathlib import Path


def reverter_para_ultimo_green(sessao_path: str | Path) -> bool:
    p = Path(sessao_path)
    if not p.exists():
        return False

    try:
        with open(p, "r", encoding="utf-8") as f:
            estado = json.load(f)

        # Checa se houve estado GREEN anterior
        historico = estado.get("historico_fases", [])
        teve_green = any(h.get("fase") == "GREEN" for h in historico)

        if not teve_green:
            return False

        agora = datetime.datetime.now().isoformat()
        estado["fase_atual"] = "GREEN"
        estado["historico_fases"].append({
            "fase": "ROLLBACK_PARA_GREEN",
            "timestamp": agora,
            "motivo": "Reversão acionada devido a falha ou quebra em refatoração"
        })

        with open(p, "w", encoding="utf-8") as f:
            json.dump(estado, f, indent=2, ensure_ascii=False)

        return True
    except Exception:
        return False
