# -*- coding: utf-8 -*-
"""
tests/test_escopo_commit.py — Escopo de ferramentas do G_TESTES_REAIS (Ticket 2, D3).

Regras sob prova em modulos/04-nucleo-compartilhado/gates/_escopo_commit.py:
  * modo padrão é 'rapido'; AIDD_GATES_MODO=completo força todas as ferramentas.
  * staged em tools/<ferramenta>/ → só aquela ferramenta.
  * staged em modulos/01-governanca-e-qualidade/gates/G_TESTES_REAIS.py ou modulos/01-governanca-e-qualidade/gates/allowlist_skipped_testes.json,
    ou caminho desconhecido sob tools/, → todas as ferramentas.
  * o gate só consulta o escopo quando AIDD_TESTES_REAIS_FERRAMENTAS está ausente.
"""

import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
ESCOPO_PATH = ROOT_DIR / "modulos" / "04-nucleo-compartilhado" / "gates" / "_escopo_commit.py"
GATE_PATH = ROOT_DIR / "modulos" / "01-governanca-e-qualidade" / "gates" / "G_TESTES_REAIS.py"

TODAS = ["aidd-forge", "aidd-planner", "aidd-pure", "aidd-master", "aidd-ops"]


@pytest.fixture(scope="session")
def escopo():
    """Módulo modulos/04-nucleo-compartilhado/gates/_escopo_commit.py carregado do disco (ausente = erro vermelho)."""
    spec = importlib.util.spec_from_file_location("_escopo_commit_testado", ESCOPO_PATH)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def _git(raiz, *args):
    return subprocess.run(
        ["git", *args], cwd=str(raiz), check=True, capture_output=True, text=True
    )


def _repo_com_staged(tmp_path, caminhos):
    """Repositório git sintético com `caminhos` escritos e staged (sem commit)."""
    raiz = tmp_path / "repo"
    raiz.mkdir()
    _git(raiz, "init", "-q")
    for caminho in caminhos:
        alvo = raiz / caminho
        alvo.parent.mkdir(parents=True, exist_ok=True)
        alvo.write_text("conteudo\n", encoding="utf-8")
    _git(raiz, "add", "-A")
    return raiz


def _ferramentas_para(escopo, raiz, **env_extra):
    arquivos = escopo.arquivos_staged(raiz=raiz)
    with pytest.MonkeyPatch.context() as mp:
        mp.delenv("AIDD_GATES_MODO", raising=False)
        for chave, valor in env_extra.items():
            mp.setenv(chave, valor)
        return escopo.ferramentas_afetadas(arquivos, TODAS)


def _alvo_do_gate(tmp_path, env_extra):
    """Roda o gate real numa árvore sintética e retorna o CompletedProcess."""
    gates = tmp_path / "gates"
    gates.mkdir()
    shutil.copy2(GATE_PATH, gates / "G_TESTES_REAIS.py")
    shutil.copy2(ESCOPO_PATH, gates / "_escopo_commit.py")

    env = os.environ.copy()
    env.pop("AIDD_TESTES_REAIS_FERRAMENTAS", None)
    env.pop("AIDD_GATES_MODO", None)
    env.update(env_extra)
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        [sys.executable, str(gates / "G_TESTES_REAIS.py")],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )


def test_modo_padrao_e_rapido(escopo, monkeypatch):
    """Sem AIDD_GATES_MODO, o modo é 'rapido'."""
    monkeypatch.delenv("AIDD_GATES_MODO", raising=False)
    assert escopo.modo() == "rapido"


def test_modo_completo_vem_do_ambiente(escopo, monkeypatch):
    """AIDD_GATES_MODO=completo troca o modo."""
    monkeypatch.setenv("AIDD_GATES_MODO", "completo")
    assert escopo.modo() == "completo"


def test_staged_em_tools_de_uma_ferramenta_restringe_o_escopo(escopo, tmp_path):
    """Staged modulos/01-governanca-e-qualidade/core/aidd-forge/x.py roda só o aidd-forge."""
    raiz = _repo_com_staged(tmp_path, ["modulos/01-governanca-e-qualidade/core/aidd-forge/x.py"])
    assert _ferramentas_para(escopo, raiz) == ["aidd-forge"]


def test_staged_no_gate_testes_reais_executa_todas(escopo, tmp_path):
    """Staged do próprio gate (com uma ferramenta staged) executa todas."""
    raiz = _repo_com_staged(tmp_path, ["modulos/01-governanca-e-qualidade/core/aidd-forge/x.py", "modulos/01-governanca-e-qualidade/gates/G_TESTES_REAIS.py"])
    assert _ferramentas_para(escopo, raiz) == TODAS


def test_staged_na_allowlist_de_skips_executa_todas(escopo, tmp_path):
    """Staged do orçamento de skipped executa todas (a regra de skip mudou)."""
    raiz = _repo_com_staged(
        tmp_path, ["modulos/01-governanca-e-qualidade/core/aidd-forge/x.py", "modulos/01-governanca-e-qualidade/gates/allowlist_skipped_testes.json"]
    )
    assert _ferramentas_para(escopo, raiz) == TODAS


def test_caminho_desconhecido_sob_tools_executa_todas(escopo, tmp_path):
    """Ferramenta sem mapeamento em tools/ não pode ser silenciosamente ignorada."""
    raiz = _repo_com_staged(tmp_path, ["modulos/01-governanca-e-qualidade/core/aidd-forge/x.py", "modulos/02-triade-motores/fluxo-09-novo/core/aidd-nova/y.py"])
    assert _ferramentas_para(escopo, raiz) == TODAS


def test_modo_completo_executa_todas_mesmo_com_staged_de_uma_ferramenta(escopo, tmp_path):
    """AIDD_GATES_MODO=completo prevalece sobre o escopo staged."""
    raiz = _repo_com_staged(tmp_path, ["modulos/01-governanca-e-qualidade/core/aidd-forge/x.py"])
    assert _ferramentas_para(escopo, raiz, AIDD_GATES_MODO="completo") == TODAS


def test_gate_usa_escopo_so_quando_ferramentas_nao_esta_definido(tmp_path):
    """Com AIDD_TESTES_REAIS_FERRAMENTAS ausente, o gate roda só a ferramenta staged."""
    ferramenta = tmp_path / "modulos" / "01-governanca-e-qualidade" / "core" / "aidd-forge"
    ferramenta.mkdir(parents=True)
    (ferramenta / "test_ok.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
    (tmp_path / "modulos" / "01-governanca-e-qualidade" / "core" / "aidd-planner").mkdir()

    _git(tmp_path, "init", "-q")
    _git(tmp_path, "add", "modulos/01-governanca-e-qualidade/core/aidd-forge/test_ok.py")

    proc = _alvo_do_gate(tmp_path, {})

    assert proc.returncode == 0, f"Falhou inesperadamente:\n{proc.stdout}\n{proc.stderr}"
    assert "[INFO] Escopo rapido: 1 ferramenta(s) alvo." in proc.stdout
    assert "aidd-planner" not in proc.stdout


def test_gate_prioriza_ferramentas_explicitas_sobre_o_escopo(tmp_path):
    """AIDD_TESTES_REAIS_FERRAMENTAS definido tem prioridade sobre o escopo staged."""
    ferramenta = tmp_path / "modulos" / "01-governanca-e-qualidade" / "core" / "aidd-planner"
    ferramenta.mkdir(parents=True)
    (ferramenta / "test_ok.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")

    _git(tmp_path, "init", "-q")
    _git(tmp_path, "add", "-A")

    proc = _alvo_do_gate(tmp_path, {"AIDD_TESTES_REAIS_FERRAMENTAS": "aidd-planner"})

    assert proc.returncode == 0, f"Falhou inesperadamente:\n{proc.stdout}\n{proc.stderr}"
    assert "[INFO] Escopo rapido: 1 ferramenta(s) alvo." in proc.stdout
    assert "aidd-planner" in proc.stdout
