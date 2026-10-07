# -*- coding: utf-8 -*-
"""Ticket 5 (ciclo-03 VSA): tools/ extinto — só o LEIA-ME de transição continua versionado (decisão A)."""

import subprocess
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]


def test_tools_so_tem_o_leia_me():
    saida = subprocess.run(["git", "ls-files", "tools"], cwd=str(RAIZ), capture_output=True, text=True, check=True)
    arquivos = [linha for linha in saida.stdout.splitlines() if linha.strip()]
    assert arquivos == ["tools/LEIA-ME.md"], f"{len(arquivos)} arquivo(s) em tools/: {arquivos[:10]}"


def test_leia_me_aponta_cada_ferramenta_para_modulos():
    texto = (RAIZ / "tools" / "LEIA-ME.md").read_text(encoding="utf-8")
    import json
    mapa = json.loads((RAIZ / "componentes/compartilhado/specs/MAPA-DONOS-FERRAMENTAS.json").read_text(encoding="utf-8"))
    for nome, dados in mapa.items():
        if isinstance(dados, dict) and "pasta" in dados:
            assert nome in texto and dados["pasta"] in texto, nome
