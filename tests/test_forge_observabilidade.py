# -*- coding: utf-8 -*-
"""
Teste de observabilidade e telemetria frugal de aidd-forge (Ticket 6 / D12 / DoD 5).
Exige:
- Falha quando uma execucao nao emite metricas estruturadas de execucao.
- Duracao e artefatos injetados registrados em JSON estrito.
- Log estruturado em secoes/ (JSONL) ou stdout.
"""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
OBS_PATH = ROOT_DIR / ".agents" / "skills" / "aidd-forge" / "scripts" / "observabilidade.py"


def carregar_observabilidade():
    spec = importlib.util.spec_from_file_location("aidd_forge_observabilidade", str(OBS_PATH))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_import_observabilidade():
    obs = carregar_observabilidade()
    assert hasattr(obs, "execucao")
    assert hasattr(obs, "validar_metrica")
    assert hasattr(obs, "MetricaAusenteError")
    assert hasattr(obs, "MetricaInvalidaError")


def test_execucao_sem_emitir_metricas_falha():
    """Run que nao emite metricas estruturadas -> falha."""
    obs = carregar_observabilidade()
    with pytest.raises(obs.MetricaAusenteError):
        with obs.execucao("forge_init"):
            pass


def test_execucao_com_metricas_emitidas_grava_em_secoes(tmp_path, capsys):
    obs = carregar_observabilidade()
    with obs.execucao("forge_init", destino_secoes=tmp_path) as run:
        run.registrar_artefato("gates/G_aidd_forge.py")
        run.registrar_artefato("hooks/pre-commit")
        metrica = run.emitir()

    assert metrica["operacao"] == "forge_init"
    assert metrica["status"] == "sucesso"
    assert metrica["duracao_s"] >= 0
    assert metrica["artefatos"] == ["gates/G_aidd_forge.py", "hooks/pre-commit"]

    arquivo = tmp_path / "FORGE-TELEMETRIA.jsonl"
    assert arquivo.is_file()
    linha = arquivo.read_text(encoding="utf-8").strip().splitlines()[-1]
    dados = json.loads(linha)
    assert dados["operacao"] == "forge_init"
    assert len(dados["artefatos"]) == 2


def test_metrica_estruturada_no_stdout(capsys):
    obs = carregar_observabilidade()
    with obs.execucao("forge_audit", destino_secoes=None) as run:
        run.registrar_artefato("relatorio.md")
        run.emitir()
    saida = capsys.readouterr().out.strip().splitlines()[-1]
    dados = json.loads(saida)
    assert dados["operacao"] == "forge_audit"
    assert set(dados) == {"operacao", "duracao_s", "artefatos", "status"}


def test_validar_metrica_rejeita_incompleta():
    obs = carregar_observabilidade()
    with pytest.raises(obs.MetricaInvalidaError):
        obs.validar_metrica({"operacao": "x"})
    with pytest.raises(obs.MetricaInvalidaError):
        obs.validar_metrica(
            {"operacao": "x", "duracao_s": -1, "artefatos": [], "status": "sucesso"}
        )
    with pytest.raises(obs.MetricaInvalidaError):
        obs.validar_metrica(
            {"operacao": "x", "duracao_s": 0.1, "artefatos": [1], "status": "sucesso"}
        )
    with pytest.raises(obs.MetricaInvalidaError):
        obs.validar_metrica(
            {"operacao": "x", "duracao_s": 0.1, "artefatos": [], "status": "indefinido"}
        )
    with pytest.raises(obs.MetricaInvalidaError):
        obs.validar_metrica(
            {"operacao": "x", "duracao_s": 0.1, "artefatos": [], "status": "sucesso", "extra": 1}
        )


def test_emitir_com_status_falha(tmp_path):
    obs = carregar_observabilidade()
    with obs.execucao("forge_conform", destino_secoes=tmp_path) as run:
        run.emitir(status="falha")
    arquivo = tmp_path / "FORGE-TELEMETRIA.jsonl"
    dados = json.loads(arquivo.read_text(encoding="utf-8").strip().splitlines()[-1])
    assert dados["status"] == "falha"


def test_subprocesso_exit_1_sem_metricas(tmp_path):
    script = tmp_path / "sem_metrica.py"
    script.write_text(
        (
            "import importlib.util, sys\n"
            f"spec = importlib.util.spec_from_file_location('obs', r'{OBS_PATH}')\n"
            "mod = importlib.util.module_from_spec(spec)\n"
            "spec.loader.exec_module(mod)\n"
            "try:\n"
            "    with mod.execucao('forge_init'):\n"
            "        pass\n"
            "    sys.exit(0)\n"
            "except mod.MetricaAusenteError:\n"
            "    sys.exit(1)\n"
        ),
        encoding="utf-8",
    )
    res = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, timeout=120)
    assert res.returncode == 1, f"esperava exit 1 sem metricas (obtido {res.returncode})"
