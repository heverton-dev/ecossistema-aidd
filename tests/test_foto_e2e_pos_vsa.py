# -*- coding: utf-8 -*-
"""Ticket 21 (ciclo-03 VSA, D12): foto E2E pós-VSA comparada com a base ciclo-01.

Red: sem a foto nova, docs/auditoria/modularizacao-vsa/ciclo-03/COMPARACAO-E2E.md não existe.
Green: o arquivo compara `ciclo-01` com uma foto tirada depois da VSA, cobre os 3 fluxos,
não tem métrica pior e, quando as pastas da foto existem nesta máquina, bate com o que
`scripts/e2e_foto.py comparar` gera de novo (o resultado não é escrito à mão).
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "e2e_foto.py"
COMPARACAO = ROOT / "docs" / "auditoria" / "modularizacao-vsa" / "ciclo-03" / "COMPARACAO-E2E.md"
FLUXOS = ("fluxo-01-pure", "fluxo-02-open", "fluxo-03-freedom")
ULTIMA_FOTO_PRE_VSA = 25  # ciclo-25 (04/10/2026): última foto antes do ciclo-03 da VSA
INICIO_POS_VSA = "2026-10-08"  # Bloco 7, o último bloco de código da VSA, entrou na main em 08/10/2026
RE_TITULO = re.compile(r"^# Comparação E2E — `(ciclo-\d+)` × `(ciclo-(\d+))`$", re.M)
RE_GERADO = re.compile(r"^> Gerado por `scripts/e2e_foto.py comparar` em (\d{4}-\d{2}-\d{2}) ", re.M)


def _texto() -> str:
    assert COMPARACAO.is_file(), f"foto E2E pós-VSA sem comparação: falta {COMPARACAO.relative_to(ROOT)}"
    return COMPARACAO.read_text(encoding="utf-8")


def _tabela(texto: str) -> list[str]:
    return [linha for linha in texto.splitlines()
            if linha.startswith("| ") and not linha.startswith("| Escopo")]


def test_comparacao_pos_vsa_contra_a_base_ciclo01_sem_piora():
    texto = _texto()
    titulo = RE_TITULO.search(texto)
    assert titulo, "título fora do formato do e2e_foto.py comparar"
    assert titulo.group(1) == "ciclo-01"
    assert int(titulo.group(3)) > ULTIMA_FOTO_PRE_VSA, f"{titulo.group(2)} não é foto pós-VSA"
    gerado = RE_GERADO.search(texto)
    assert gerado and gerado.group(1) >= INICIO_POS_VSA
    linhas = _tabela(texto)
    for fluxo in FLUXOS:
        assert any(linha.startswith(f"| {fluxo} | exit_code |") for linha in linhas), fluxo
    assert [linha for linha in linhas if "| SIM |" in linha] == []
    assert "- Exit 0" in texto


def test_comparacao_bate_com_o_comparar_rodado_de_novo(tmp_path):
    sys.path.insert(0, str(ROOT / "scripts"))
    import e2e_foto

    texto = _texto()
    titulo = RE_TITULO.search(texto)
    assert titulo
    raiz = e2e_foto.raiz_padrao()
    base, novo = raiz / titulo.group(1), raiz / titulo.group(2)
    if not all((c / "fluxo-01-pure" / "RESULTADO-E2E.json").is_file() for c in (base, novo)):
        pytest.skip(f"pastas da foto E2E fora desta máquina: {raiz}")
    saida = tmp_path / "COMPARACAO-E2E.md"
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "comparar", "--base", str(base), "--novo", str(novo),
         "--saida", str(saida)],
        cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert _tabela(saida.read_text(encoding="utf-8")) == _tabela(texto)
