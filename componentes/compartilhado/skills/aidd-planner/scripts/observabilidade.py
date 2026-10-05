# -*- coding: utf-8 -*-
"""
Observabilidade e métricas de blueprint para aidd-planner-runner (D12).
"""

import json
from pathlib import Path
from typing import Dict, Any


class RastreadorPlanner:
    def __init__(self, caminho_planner: Path | str):
        self.caminho = Path(caminho_planner).resolve()

    def coletar_metricas(self) -> Dict[str, Any]:
        if not self.caminho.exists():
            return {"valido": False, "erro": "Arquivo inexistente"}

        try:
            conteudo_str = self.caminho.read_text(encoding="utf-8")
            dados = json.loads(conteudo_str)
        except Exception as e:
            return {"valido": False, "erro": str(e)}

        bc = dados.get("bounded_contexts", [])
        entidades = dados.get("entidades", [])
        rotas = dados.get("rotas", [])

        tokens_estimados = max(1, len(conteudo_str) // 4)

        return {
            "valido": True,
            "arquivo": str(self.caminho),
            "total_bounded_contexts": len(bc) if isinstance(bc, list) else 0,
            "total_entidades": len(entidades) if isinstance(entidades, list) else 0,
            "total_rotas": len(rotas) if isinstance(rotas, list) else 0,
            "tamanho_bytes": len(conteudo_str.encode("utf-8")),
            "tokens_estimados": tokens_estimados,
        }
