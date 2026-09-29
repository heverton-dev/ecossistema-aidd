# -*- coding: utf-8 -*-
"""
Teste da observabilidade de aidd-enterprise (Ticket 6 / D12).
Exige:
- Log de telemetria estruturado persistido em secoes/ apos a injecao;
  ausencia de metrica -> exit 1.
- Metricas: inicio, fim, duracao, contagem de componentes, bytes transferidos
  e hashes verificados (SHA-256).
"""

import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
OBS_PATH = ROOT_DIR / ".agents" / "skills" / "aidd-enterprise" / "scripts" / "observabilidade.py"
ARQUIVO_TELEMETRIA = "ENTERPRISE-TELEMETRIA.jsonl"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def carregar_observabilidade():
    spec = importlib.util.spec_from_file_location("aidd_enterprise_observabilidade", str(OBS_PATH))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class RelogioFalso:
    """Relogio deterministico para teste de inicio/fim/duracao."""

    def __init__(self, passos):
        self.passos = list(passos)

    def __call__(self) -> float:
        if len(self.passos) > 1:
            return self.passos.pop(0)
        return self.passos[0]


def test_import_observabilidade():
    obs = carregar_observabilidade()
    assert hasattr(obs, "validar_metrica")
    assert hasattr(obs, "execucao")
    assert hasattr(obs, "Execucao")
    assert hasattr(obs, "MetricaAusenteError")
    assert hasattr(obs, "MetricaInvalidaError")


def test_execucao_sem_emitir_metricas_falha():
    """Injecao sem log de telemetria estruturado -> exit 1 (MetricaAusenteError)."""
    obs = carregar_observabilidade()
    with pytest.raises(obs.MetricaAusenteError):
        with obs.execucao("enterprise_inject", destino_secoes=None):
            pass


def test_metrica_registra_inicio_fim_duracao_e_volumetria(tmp_path):
    obs = carregar_observabilidade()
    relogio = RelogioFalso([100.0, 112.5])
    with obs.execucao("enterprise_inject", destino_secoes=tmp_path, clock=relogio) as run:
        run.registrar_componente("skill/auth")
        run.registrar_componente("rule/segredos")
        run.registrar_bytes(2048)
        run.registrar_hash("a" * 64)
        run.registrar_hash("b" * 64)
        metrica = run.emitir()

    assert metrica["inicio_s"] == 100.0
    assert metrica["fim_s"] == 112.5
    assert metrica["duracao_s"] == pytest.approx(12.5)
    assert metrica["componentes"] == 2
    assert metrica["bytes_transferidos"] == 2048
    assert metrica["hashes_verificados"] == ["a" * 64, "b" * 64]
    assert metrica["status"] == "sucesso"


def test_log_persistido_em_secoes_jsonl(tmp_path):
    obs = carregar_observabilidade()
    destino = tmp_path / "secoes"
    with obs.execucao("enterprise_inject", destino_secoes=destino) as run:
        run.registrar_componente("mcp/servidor")
        run.registrar_bytes(128)
        run.registrar_hash("c" * 64)
        run.emitir()

    arquivo = destino / ARQUIVO_TELEMETRIA
    assert arquivo.is_file(), "telemetria deve ser persistida em secoes/"
    linhas = arquivo.read_text(encoding="utf-8").splitlines()
    assert len(linhas) == 1
    registro = json.loads(linhas[0])
    assert registro["operacao"] == "enterprise_inject"
    assert registro["componentes"] == 1
    assert registro["bytes_transferidos"] == 128
    assert SHA256_RE.match(registro["hashes_verificados"][0])
    assert registro["fim_s"] >= registro["inicio_s"]


def test_destino_padrao_e_secoes_do_repositorio():
    """Sem destino explicito, a telemetria vai para secoes/ do repositorio."""
    obs = carregar_observabilidade()
    assert obs.destino_padrao_secoes() == ROOT_DIR / "secoes"


def test_status_falha_e_persistido(tmp_path):
    obs = carregar_observabilidade()
    with obs.execucao("enterprise_inject", destino_secoes=tmp_path) as run:
        run.emitir("falha")
    arquivo = tmp_path / ARQUIVO_TELEMETRIA
    registro = json.loads(arquivo.read_text(encoding="utf-8").splitlines()[0])
    assert registro["status"] == "falha"


@pytest.mark.parametrize(
    "troca",
    [
        {"inicio_s": "agora"},
        {"fim_s": None},
        {"duracao_s": -1},
        {"componentes": "dois"},
        {"bytes_transferidos": -5},
        {"hashes_verificados": ["nao-e-hash"]},
        {"hashes_verificados": "abc"},
        {"status": "talvez"},
    ],
)
def test_validar_metrica_rejeita_incompleta(troca):
    obs = carregar_observabilidade()
    metrica = {
        "operacao": "enterprise_inject",
        "inicio_s": 1.0,
        "fim_s": 2.0,
        "duracao_s": 1.0,
        "componentes": 0,
        "bytes_transferidos": 0,
        "hashes_verificados": [],
        "status": "sucesso",
    }
    metrica.update(troca)
    with pytest.raises(obs.MetricaInvalidaError):
        obs.validar_metrica(metrica)


def test_subprocesso_exit_1_sem_telemetria(tmp_path):
    """End-to-end: injecao sem log estruturado -> exit 1; com log -> exit 0."""
    sem_log = tmp_path / "sem_log.py"
    sem_log.write_text(
        (
            "import importlib.util, sys\n"
            f"spec = importlib.util.spec_from_file_location('obs', r'{OBS_PATH}')\n"
            "mod = importlib.util.module_from_spec(spec)\n"
            "spec.loader.exec_module(mod)\n"
            "try:\n"
            f"    with mod.execucao('enterprise_inject', destino_secoes=r'{tmp_path / 'secoes'}'):\n"
            "        pass\n"
            "    sys.exit(0)\n"
            "except mod.MetricaAusenteError:\n"
            "    sys.exit(1)\n"
        ),
        encoding="utf-8",
    )
    res_sem = subprocess.run([sys.executable, str(sem_log)], capture_output=True, text=True, timeout=60)
    assert res_sem.returncode == 1, f"injecao sem telemetria deve terminar com exit 1 (obtido {res_sem.returncode})"
    assert not (tmp_path / "secoes" / ARQUIVO_TELEMETRIA).exists()

    com_log = tmp_path / "com_log.py"
    com_log.write_text(
        (
            "import importlib.util, sys\n"
            f"spec = importlib.util.spec_from_file_location('obs', r'{OBS_PATH}')\n"
            "mod = importlib.util.module_from_spec(spec)\n"
            "spec.loader.exec_module(mod)\n"
            f"with mod.execucao('enterprise_inject', destino_secoes=r'{tmp_path / 'secoes'}') as run:\n"
            "    run.registrar_componente('skill/x')\n"
            "    run.registrar_bytes(10)\n"
            "    run.registrar_hash('d' * 64)\n"
            "    run.emitir()\n"
            "sys.exit(0)\n"
        ),
        encoding="utf-8",
    )
    res_com = subprocess.run([sys.executable, str(com_log)], capture_output=True, text=True, timeout=60)
    assert res_com.returncode == 0, f"com telemetria deve terminar com exit 0 (obtido {res_com.returncode})"
    assert (tmp_path / "secoes" / ARQUIVO_TELEMETRIA).is_file()
