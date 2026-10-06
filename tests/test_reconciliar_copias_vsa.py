# -*- coding: utf-8 -*-
"""Ticket 1 (ciclo-03 VSA): relatório de divergência entre tools/ e modulos/."""

import json
import subprocess
import sys
from pathlib import Path

RAIZ_REPO = Path(__file__).resolve().parents[1]
SCRIPT = RAIZ_REPO / "scripts" / "reconciliar_copias_vsa.py"


def _gravar(caminho: Path, conteudo: str, eol: str = "\n") -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_bytes(conteudo.replace("\n", eol).encode("utf-8"))


def _repo_temporario(tmp_path: Path) -> Path:
    raiz = tmp_path / "repo"
    ferramenta = raiz / "tools" / "aidd-forge"
    canonica = raiz / "modulos" / "01-governanca-e-qualidade" / "core" / "aidd-forge"
    _gravar(ferramenta / "igual.py", "x = 1\n")
    _gravar(canonica / "igual.py", "x = 1\n", eol="\r\n")  # CRLF não conta como diferença
    _gravar(ferramenta / "diferente.py", "y = 1\n")
    _gravar(canonica / "diferente.py", "y = 2\n")
    _gravar(ferramenta / "so_tools.py", "z = 1\n")
    _gravar(canonica / "so_modulos.py", "w = 1\n")
    _gravar(ferramenta / "__pycache__" / "lixo.pyc", "cache\n")
    subprocess.run(["git", "init", "-q"], cwd=raiz, check=True)
    subprocess.run(["git", "add", "-A", "-f"], cwd=raiz, check=True)
    return raiz


def _rodar(raiz: Path, saida: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--raiz", str(raiz), "--saida", str(saida), *extra],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )


def test_exigir_zero_reprova_e_lista_divergente_e_so_tools(tmp_path):
    raiz = _repo_temporario(tmp_path)
    saida = tmp_path / "DIVERGENCIAS.json"
    proc = _rodar(raiz, saida, "--exigir-zero")
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "aidd-forge/diferente.py" in proc.stdout
    assert "aidd-forge/so_tools.py" in proc.stdout

    relatorio = json.loads(saida.read_text(encoding="utf-8"))
    forge = relatorio["ferramentas"]["aidd-forge"]
    assert forge["divergentes"] == ["diferente.py"]
    assert forge["so_tools"] == ["so_tools.py"]
    assert forge["so_modulos"] == ["so_modulos.py"]
    assert forge["identicos"] == 1
    assert relatorio["totais"]["divergentes"] == 1
    assert relatorio["totais"]["so_tools"] == 1


def test_sem_exigir_zero_sai_com_zero_e_grava_relatorio(tmp_path):
    raiz = _repo_temporario(tmp_path)
    saida = tmp_path / "DIVERGENCIAS.json"
    proc = _rodar(raiz, saida)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert saida.exists()


def test_exigir_zero_passa_quando_copias_iguais(tmp_path):
    raiz = tmp_path / "repo"
    _gravar(raiz / "tools" / "aidd-ops" / "a.py", "a = 1\n")
    _gravar(raiz / "modulos" / "03-plataforma-e-entrega" / "operacoes-ops" / "aidd-ops" / "a.py", "a = 1\n")
    subprocess.run(["git", "init", "-q"], cwd=raiz, check=True)
    subprocess.run(["git", "add", "-A"], cwd=raiz, check=True)
    proc = _rodar(raiz, tmp_path / "out.json", "--exigir-zero")
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_mapa_inclui_planner_na_governanca():
    sys.path.insert(0, str(RAIZ_REPO / "scripts"))
    try:
        import reconciliar_copias_vsa as mod
    finally:
        sys.path.pop(0)
    assert mod.MAPA_CANONICO["aidd-planner"] == "modulos/01-governanca-e-qualidade/core/aidd-planner"
    assert len(mod.MAPA_CANONICO) == 8


def test_linha_base_de_testes_e_preservada(tmp_path):
    raiz = _repo_temporario(tmp_path)
    saida = tmp_path / "DIVERGENCIAS.json"
    _rodar(raiz, saida, "--linha-base-testes", "1234")
    _rodar(raiz, saida)
    assert json.loads(saida.read_text(encoding="utf-8"))["linha_base_testes_passando"] == 1234
