# -*- coding: utf-8 -*-
"""
Observabilidade, métricas e frugalidade para aidd-plan (D12).
"""

from pathlib import Path
from typing import Dict, Any


class RastreadorPlano:
    def __init__(self, pasta_plano: Path | str):
        self.pasta = Path(pasta_plano).resolve()

    def coletar_metricas(self) -> Dict[str, Any]:
        if not self.pasta.exists() or not self.pasta.is_dir():
            return {
                "valido": False,
                "erro": f"Pasta {self.pasta} inexistente ou inválida."
            }

        arquivos_md = list(self.pasta.glob("*.md"))
        itens = [f for f in arquivos_md if f.name != "00-PROCESSO-E-DECISOES.md"]

        total_linhas = 0
        total_caracteres = 0

        for f in arquivos_md:
            conteudo = f.read_text(encoding="utf-8", errors="replace")
            linhas = conteudo.splitlines()
            total_linhas += len(linhas)
            total_caracteres += len(conteudo)

        # Estimativa de tokens: ~4 caracteres por token
        tokens_estimados = max(1, total_caracteres // 4)

        return {
            "valido": True,
            "pasta": str(self.pasta),
            "total_arquivos": len(arquivos_md),
            "total_itens": len(itens),
            "total_linhas": total_linhas,
            "total_caracteres": total_caracteres,
            "tokens_estimados": tokens_estimados,
        }
