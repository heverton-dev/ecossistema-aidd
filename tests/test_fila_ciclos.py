# -*- coding: utf-8 -*-
"""
Ticket 7 do ciclo agilidade-gates: um ciclo pesado por vez + aviso ao terminar.

Regressão (30/09/2026): até 4 ciclos 4F rodavam juntos em 16 GB; a falta de memória
derrubou processos, e o fim de cada ciclo dependia de alguém "voltar em 30 minutos".
"""

import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import fila_ciclos  # noqa: E402


def _pid_morto() -> int:
    proc = subprocess.Popen([sys.executable, "-c", "pass"])
    proc.wait()
    return proc.pid


def test_segundo_ciclo_espera_o_primeiro_liberar(tmp_path):
    fila_ciclos.adquirir("ciclo-a", tmp_path, intervalo_s=0.05)
    avisos, tomou = [], threading.Event()

    def segundo():
        fila_ciclos.adquirir("ciclo-b", tmp_path, intervalo_s=0.05, avisar=avisos.append)
        tomou.set()

    # Mesmo processo = mesmo pid: simula o dono vivo trocando o pid da trava pelo do pytest.
    t = threading.Thread(target=segundo, daemon=True)
    t.start()
    time.sleep(0.3)
    assert not tomou.is_set(), "segundo ciclo não pode rodar enquanto o primeiro segura a fila"
    assert any("Aguardando 'ciclo-a'" in a for a in avisos)

    fila_ciclos.liberar("ciclo-a", "concluido", tmp_path, notificador=lambda t, m: True)
    t.join(timeout=5)
    assert tomou.is_set()
    assert json.loads((tmp_path / fila_ciclos.TRAVA).read_text(encoding="utf-8"))["ciclo"] == "ciclo-b"


def test_trava_de_processo_morto_e_liberada(tmp_path):
    trava = tmp_path / fila_ciclos.TRAVA
    trava.parent.mkdir(parents=True)
    trava.write_text(json.dumps({"pid": _pid_morto(), "ciclo": "ciclo-velho", "inicio": "x"}), encoding="utf-8")
    avisos = []

    fila_ciclos.adquirir("ciclo-novo", tmp_path, intervalo_s=0.05, avisar=avisos.append, timeout_s=5)

    assert json.loads(trava.read_text(encoding="utf-8"))["ciclo"] == "ciclo-novo"
    assert any("órfã" in a and "ciclo-velho" in a for a in avisos)


def test_processo_vivo_nao_mata_nem_confunde(tmp_path):
    assert fila_ciclos.processo_vivo(os.getpid()) is True
    assert fila_ciclos.processo_vivo(_pid_morto()) is False
    assert fila_ciclos.processo_vivo(0) is False


@pytest.mark.parametrize("codigo, esperado", [(0, "concluido"), (1, "reprovado")])
def test_fim_do_ciclo_grava_resultado_e_avisa_mesmo_com_sys_exit(tmp_path, codigo, esperado):
    avisos = []
    with pytest.raises(SystemExit):
        with fila_ciclos.ciclo_pesado("ciclo-x", tmp_path, notificador=lambda t, m: avisos.append((t, m))):
            sys.exit(codigo)

    assert not (tmp_path / fila_ciclos.TRAVA).exists()
    registro = json.loads((tmp_path / fila_ciclos.ULTIMO_CICLO).read_text(encoding="utf-8"))
    assert registro["ciclo"] == "ciclo-x" and registro["resultado"] == esperado
    assert avisos and esperado in avisos[0][0]


def test_liberar_nao_solta_trava_de_outro_processo(tmp_path):
    trava = tmp_path / fila_ciclos.TRAVA
    trava.parent.mkdir(parents=True)
    trava.write_text(json.dumps({"pid": os.getpid() + 999999, "ciclo": "alheio", "inicio": "x"}), encoding="utf-8")
    fila_ciclos.liberar("meu", "concluido", tmp_path, notificador=lambda t, m: True)
    assert trava.exists()


def test_orquestrador_usa_a_fila():
    fonte = (ROOT / "scripts" / "orquestrador_4f.py").read_text(encoding="utf-8")
    assert "fila_ciclos.ciclo_pesado(pipeline_id, repo_root)" in fonte
