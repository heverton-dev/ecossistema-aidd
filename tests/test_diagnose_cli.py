# -*- coding: utf-8 -*-
"""
Testes da CLI do aidd-diagnose (`python ecossistema.py diagnose ...`).

Todo teste roda com AIDD_DIAGNOSE_RAIZ apontando para tmp_path: nada é
gravado nem apagado em docs/diagnosticos/ do repositório real.
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def diagnose(raiz: Path, *args: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "AIDD_DIAGNOSE_RAIZ": str(raiz), "PYTHONUTF8": "1"}
    return subprocess.run(
        [sys.executable, str(ROOT / "ecossistema.py"), "diagnose", *args],
        cwd=str(ROOT), capture_output=True, text=True, env=env,
        encoding="utf-8", errors="replace",
    )


def sessoes(raiz: Path) -> list:
    return sorted((raiz / "docs" / "diagnosticos").glob("*_*"))


def test_iniciar_com_sintoma_cria_sessao_json(tmp_path):
    res = diagnose(tmp_path, "iniciar", "--sintoma", "Teste de diagnose")
    assert res.returncode == 0, res.stdout + res.stderr

    [pasta] = sessoes(tmp_path)
    assert pasta.name.endswith("_teste-de-diagnose")
    data = json.loads((pasta / "sessao.json").read_text(encoding="utf-8"))
    assert data["sintoma"] == "Teste de diagnose"
    assert data["fase_atual"] == 1


def test_iniciar_sem_sintoma_falha(tmp_path):
    assert diagnose(tmp_path, "iniciar").returncode != 0
    assert sessoes(tmp_path) == []


def test_fase_rejeita_sem_sessao_anterior(tmp_path):
    res = diagnose(tmp_path, "fase", "--numero", "2")
    assert res.returncode == 1
    assert "Nenhuma sessão" in res.stdout


def test_fase_rejeita_pular_fase(tmp_path):
    assert diagnose(tmp_path, "iniciar", "--sintoma", "pulo").returncode == 0
    res = diagnose(tmp_path, "fase", "--numero", "3")
    assert res.returncode == 1
    assert "Complete a fase 2" in res.stdout


def test_fase_aceita_progressao_sequencial(tmp_path):
    assert diagnose(tmp_path, "iniciar", "--sintoma", "Test sequence").returncode == 0
    assert diagnose(tmp_path, "fase", "--numero", "2").returncode == 0
    assert diagnose(tmp_path, "fase", "--numero", "3").returncode == 0

    [pasta] = sessoes(tmp_path)
    data = json.loads((pasta / "sessao.json").read_text(encoding="utf-8"))
    assert data["fase_atual"] == 3
    assert data["fases_completadas"] == [1, 2, 3]


def test_fase_avanca_a_sessao_mais_recente_nao_a_ultima_em_ordem_alfabetica(tmp_path):
    """Regressão: com duas sessões no mesmo dia, 'fase' usava a de nome maior (zebra)."""
    assert diagnose(tmp_path, "iniciar", "--sintoma", "zebra antiga").returncode == 0
    time.sleep(0.05)
    assert diagnose(tmp_path, "iniciar", "--sintoma", "abelha nova").returncode == 0

    res = diagnose(tmp_path, "fase", "--numero", "2")
    assert res.returncode == 0, res.stdout
    assert "abelha-nova" in res.stdout

    por_nome = {p.name.split("_", 1)[1]: p for p in sessoes(tmp_path)}
    nova = json.loads((por_nome["abelha-nova"] / "sessao.json").read_text(encoding="utf-8"))
    antiga = json.loads((por_nome["zebra-antiga"] / "sessao.json").read_text(encoding="utf-8"))
    assert nova["fase_atual"] == 2
    assert antiga["fase_atual"] == 1


def test_registrar_e_relatorio_geram_relatorio_aceito_pelo_gate(tmp_path):
    """Fluxo ligado de ponta a ponta: CLI -> observabilidade -> G_aidd_diagnose."""
    teste_regressao = tmp_path / "test_regressao_ok.py"
    teste_regressao.write_text("def test_ok():\n    assert 1 + 1 == 2\n", encoding="utf-8")

    assert diagnose(tmp_path, "iniciar", "--sintoma", "fluxo completo").returncode == 0
    res = diagnose(tmp_path, "registrar", "--fase", "1", "--comando", "pytest tests/x.py -k falha")
    assert res.returncode == 0, res.stdout + res.stderr
    res = diagnose(tmp_path, "registrar", "--fase", "3", "--hipotese", "campo nulo quando Y não inicia")
    assert res.returncode == 0, res.stdout + res.stderr
    res = diagnose(
        tmp_path, "relatorio", "--execucoes", "3",
        "--teste-regressao", str(teste_regressao), "--exit-antes", "1",
    )
    assert res.returncode == 0, res.stdout + res.stderr

    [pasta] = sessoes(tmp_path)
    relatorio = pasta / "RELATORIO-CAUSA-RAIZ.md"
    assert relatorio.is_file()

    gate = subprocess.run(
        [sys.executable, str(ROOT / "gates" / "G_aidd_diagnose.py"), "--relatorio", str(relatorio)],
        cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    assert gate.returncode == 0, gate.stdout


def test_registrar_descartada_exige_prova(tmp_path):
    assert diagnose(tmp_path, "iniciar", "--sintoma", "sem prova").returncode == 0
    res = diagnose(tmp_path, "registrar", "--fase", "4", "--descartada", "DNS")
    assert res.returncode == 1


@pytest.mark.parametrize("sub", ["registrar --fase 1", "relatorio"])
def test_subcomandos_sem_sessao_falham(tmp_path, sub):
    assert diagnose(tmp_path, *sub.split()).returncode == 1


def test_repositorio_real_intocado(tmp_path):
    """Prova que o override funciona: docs/diagnosticos do repo não muda."""
    real = ROOT / "docs" / "diagnosticos"
    antes = sorted(p.as_posix() for p in real.rglob("*")) if real.exists() else []
    assert diagnose(tmp_path, "iniciar", "--sintoma", "nao tocar repo").returncode == 0
    depois = sorted(p.as_posix() for p in real.rglob("*")) if real.exists() else []
    assert antes == depois
