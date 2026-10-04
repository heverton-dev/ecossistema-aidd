# -*- coding: utf-8 -*-
"""
Testes de contar_duplicatas.py (Ticket 19 — D15 / DoD 8).

Garante que não existem cópias de peças do catálogo dentro de tools/.
Baseline no início da auditoria: 249 conteúdos repetidos em 727 arquivos, 126 cópias de gate.
"""

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "contar_duplicatas.py"


def test_zero_copias_de_pecas_do_catalogo_sob_tools():
    """Garante que nenhuma peça do catálogo do almoxarifado esteja copiada sob tools/."""
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    import contar_duplicatas

    resultado = contar_duplicatas.analisar_duplicatas(REPO_ROOT)
    copias_catalogo_sob_tools = resultado.get("copias_catalogo_sob_tools", [])

    assert len(copias_catalogo_sob_tools) == 0, (
        f"Encontradas {len(copias_catalogo_sob_tools)} cópias de peças do catálogo sob tools/:\n"
        + "\n".join(f"  - {c}" for c in copias_catalogo_sob_tools)
    )


def test_script_contar_duplicatas_cli_emite_json_valido():
    """Garante que a CLI de contar_duplicatas.py emite JSON com as métricas esperadas."""
    proc = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--raiz", str(REPO_ROOT)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert proc.returncode == 0, proc.stderr
    dados = json.loads(proc.stdout)
    assert "total_blobs_analisados" in dados
    assert "copias_catalogo_sob_tools_total" in dados
    assert dados["copias_catalogo_sob_tools_total"] == 0
