# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — SUBGRAFOS FEDERADOS DO CODEBASE-MEMORY-MCP (VSA)
=============================================================================
Particionamento lógico de domínio em subgrafos federados com isolamento de
bounded context para evitar contenção e sobrecarga de memória.
=============================================================================
"""

import os
import sys
import json
import shutil
import subprocess
from typing import Dict, List, Optional, Any

# Nomes do padrão (docs/padroes/ARQUITETURA-MODULARIZACAO-VSA-ECOSSISTEMA.md §7, ciclo-03 T19).
# Plataforma = enterprise + master + ops; scripts/ fica no grafo do repositório inteiro.
DOMINIOS_VSA = {
    "aidd-nucleo": "modulos/04-nucleo-compartilhado",
    "modulo-governanca": "modulos/01-governanca-e-qualidade",
    "triade-fluxo-pure": "modulos/02-triade-motores/fluxo-01-pure",
    "triade-fluxo-open": "modulos/02-triade-motores/fluxo-02-open",
    "triade-fluxo-freedom": "modulos/02-triade-motores/fluxo-03-freedom",
    "modulo-plataforma-ops": "modulos/03-plataforma-e-entrega",
}


def resolver_cbm_bin() -> str:
    cmd = shutil.which("codebase-memory-mcp")
    if cmd:
        return cmd
    custom = r"C:\Users\trcnologia\tools\codebase-memory-mcp\codebase-memory-mcp.exe"
    if os.path.isfile(custom):
        return custom
    return "codebase-memory-mcp"


class SubgrafoFederadoVSA:
    """Gerenciador e orquestrador de subgrafos federados por domínio VSA."""

    def __init__(self, raiz_repo: Optional[str] = None):
        self.raiz_repo = os.path.abspath(raiz_repo or os.getcwd())
        self.cbm_bin = resolver_cbm_bin()

    def obter_dominio_de_caminho(self, caminho_rel: str) -> str:
        """Determina a qual subgrafo federado um caminho pertence."""
        caminho_norm = caminho_rel.replace("\\", "/").strip("/")
        for dominio, prefixo in DOMINIOS_VSA.items():
            if caminho_norm.startswith(prefixo):
                return dominio
        return "global"

    def listar_dominios(self) -> Dict[str, str]:
        """Retorna mapa de subgrafos federados ativos."""
        return dict(DOMINIOS_VSA)

    def indexar_subgrafo(self, dominio: str, modo: str = "moderate") -> Dict[str, Any]:
        """Indexa separadamente um subgrafo federado por bounded context."""
        if dominio not in DOMINIOS_VSA and dominio != "global":
            return {
                "sucesso": False,
                "erro": f"Domínio '{dominio}' não reconhecido nos subgrafos federados.",
            }

        rel_path = DOMINIOS_VSA.get(dominio, "")
        alvo_path = os.path.join(self.raiz_repo, rel_path)
        nome_subgrafo = f"vsa-{dominio}"

        cmd = [
            self.cbm_bin,
            "cli",
            "index_repository",
            "--repo-path",
            alvo_path,
            "--name",
            nome_subgrafo,
            "--mode",
            modo,
        ]

        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
            return {
                "sucesso": res.returncode == 0,
                "dominio": dominio,
                "nome_subgrafo": nome_subgrafo,
                "exit_code": res.returncode,
                "stdout": res.stdout.strip(),
                "stderr": res.stderr.strip(),
            }
        except Exception as exc:
            return {
                "sucesso": False,
                "dominio": dominio,
                "erro": str(exc),
            }

    def indexar_todos(self, modo: str = "fast") -> Dict[str, Any]:
        """Indexa todos os subgrafos federados de cada módulo e submódulo."""
        resultados = {}
        for dom in DOMINIOS_VSA:
            res = self.indexar_subgrafo(dom, modo=modo)
            resultados[dom] = res
        return resultados


if __name__ == "__main__":
    fed = SubgrafoFederadoVSA()
    print(json.dumps({"dominios": fed.listar_dominios()}, indent=2))
