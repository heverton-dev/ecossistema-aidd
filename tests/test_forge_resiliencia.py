# -*- coding: utf-8 -*-
"""
Teste de resiliencia operacional de aidd-forge (Ticket 5 / D11 / DoD 4).
Exige:
- Retry com backoff exponencial para erros transientes (IO permission, git lock).
- Falha abrupta (sem retry) para erros nao transientes.
- Esgotamento de tentativas -> ResilienciaEsgotadaError.
- Tratamento estruturado de falhas (registro + persistencia JSONL).
"""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
RES_PATH = ROOT_DIR / ".agents" / "skills" / "aidd-forge" / "scripts" / "resiliencia.py"


def carregar_resiliencia():
    spec = importlib.util.spec_from_file_location("aidd_forge_resiliencia", str(RES_PATH))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_import_resiliencia():
    res = carregar_resiliencia()
    assert hasattr(res, "com_retry")
    assert hasattr(res, "eh_transiente")
    assert hasattr(res, "registrar_falha")
    assert hasattr(res, "persistir_falha")
    assert hasattr(res, "ResilienciaEsgotadaError")


def test_retry_recupera_de_erro_de_permissao():
    res = carregar_resiliencia()
    chamadas = {"n": 0}

    def operacao_instavel():
        chamadas["n"] += 1
        if chamadas["n"] < 3:
            raise PermissionError("sem permissao de escrita (transiente)")
        return "ok"

    esperas = []
    assert res.com_retry(operacao_instavel, tentativas=4, esperar=esperas.append) == "ok"
    assert chamadas["n"] == 3
    assert len(esperas) == 2


def test_backoff_exponencial_e_deterministico():
    res = carregar_resiliencia()
    esperas = []
    contador = {"n": 0}

    def sempre_falha():
        contador["n"] += 1
        raise PermissionError("index.lock: Permission denied")

    with pytest.raises(res.ResilienciaEsgotadaError):
        res.com_retry(
            sempre_falha,
            tentativas=4,
            backoff_base=0.1,
            fator=2.0,
            esperar=esperas.append,
        )
    assert esperas == [0.1, 0.2, 0.4]
    assert contador["n"] == 4


def test_erro_nao_transiente_falha_abruptamente_sem_retry():
    res = carregar_resiliencia()
    chamadas = {"n": 0}

    def operacao_invalida():
        chamadas["n"] += 1
        raise ValueError("erro de logica, nao transiente")

    esperas = []
    with pytest.raises(ValueError):
        res.com_retry(operacao_invalida, tentativas=5, esperar=esperas.append)
    assert chamadas["n"] == 1, "erro nao transiente nao pode ser retentado"
    assert esperas == []


def test_travamento_git_e_tratado_como_transiente():
    res = carregar_resiliencia()
    erro = OSError("Unable to create '.git/index.lock': Permission denied")
    assert res.eh_transiente(erro) is True
    assert res.eh_transiente(PermissionError("negado")) is True
    assert res.eh_transiente(ValueError("bug proprio")) is False


def test_git_lock_retentado_ate_sucesso():
    res = carregar_resiliencia()
    tentativas = {"n": 0}

    def git_instavel():
        tentativas["n"] += 1
        if tentativas["n"] == 1:
            raise OSError("Unable to create '.git/index.lock': Resource temporarily unavailable")
        return 0

    esperas = []
    assert res.com_retry(git_instavel, tentativas=3, esperar=esperas.append) == 0
    assert tentativas["n"] == 2
    assert len(esperas) == 1


def test_registro_estruturado_de_falha():
    res = carregar_resiliencia()
    registro = res.registrar_falha(
        erro=PermissionError("negado"),
        tentativas=3,
        contexto={"operacao": "forge_init", "alvo": "/tmp/x"},
    )
    assert registro["tipo"] == "PermissionError"
    assert registro["transiente"] is True
    assert registro["tentativas"] == 3
    assert registro["contexto"]["operacao"] == "forge_init"
    assert "mensagem" in registro


def test_persistir_falha_grava_jsonl(tmp_path):
    res = carregar_resiliencia()
    registro = res.registrar_falha(erro=OSError("lock"), tentativas=2, contexto={"op": "git"})
    caminho = res.persistir_falha(tmp_path, registro)
    assert caminho.is_file()
    linhas = caminho.read_text(encoding="utf-8").strip().splitlines()
    assert len(linhas) == 1
    dados = json.loads(linhas[0])
    assert dados["tentativas"] == 2
    assert dados["tipo"] == "OSError"


def test_subprocesso_exit_0_quando_recupera_e_exit_1_quando_esgota(tmp_path):
    script = tmp_path / "provar_resiliencia.py"
    script.write_text(
        (
            "import importlib.util, sys\n"
            f"spec = importlib.util.spec_from_file_location('res', r'{RES_PATH}')\n"
            "mod = importlib.util.module_from_spec(spec)\n"
            "spec.loader.exec_module(mod)\n"
            "estado = {'n': 0}\n"
            "def instavel():\n"
            "    estado['n'] += 1\n"
            "    if estado['n'] < 2:\n"
            "        raise PermissionError('transiente')\n"
            "    return 'ok'\n"
            "try:\n"
            "    mod.com_retry(instavel, tentativas=3, esperar=lambda s: None)\n"
            "except Exception:\n"
            "    sys.exit(9)\n"
            "try:\n"
            "    mod.com_retry(lambda: (_ for _ in ()).throw(PermissionError('sempre')), tentativas=2, esperar=lambda s: None)\n"
            "except mod.ResilienciaEsgotadaError:\n"
            "    sys.exit(1)\n"
            "sys.exit(0)\n"
        ),
        encoding="utf-8",
    )
    res = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, timeout=120)
    assert res.returncode == 1, f"esperava exit 1 ao esgotar tentativas (obtido {res.returncode})"
