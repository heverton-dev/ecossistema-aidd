# -*- coding: utf-8 -*-
"""Ticket 16 (ciclo-03 VSA): micro-gates por subfatia, só com prefixos de modulos/.

Antecipado no Bloco 2: o comando antigo (pytest da fatia inteira a partir da raiz)
quebrava na coleta e barrava qualquer commit em modulos/.
"""

import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from scripts.micro_gates import FATIAS_MAPA, comando_suite  # noqa: E402

FERRAMENTAS = {"aidd-forge", "aidd-planner", "aidd-pure", "aidd-open", "aidd-freedom",
               "aidd-enterprise", "aidd-master", "aidd-ops"}


def _suites():
    return [suite for config in FATIAS_MAPA.values() for suite in config.get("suites", [])]


def test_prefixos_so_em_modulos_ou_raiz():
    for fatia, config in FATIAS_MAPA.items():
        for prefixo in config["prefixo"]:
            assert not prefixo.startswith("tools/"), f"{fatia}: prefixo legado {prefixo}"


def test_uma_suite_por_subfatia_cobrindo_as_8_ferramentas():
    suites = _suites()
    assert len(suites) == len(set(suites)), "suíte repetida"
    assert {Path(s).name for s in suites} == FERRAMENTAS
    for suite in suites:
        assert (RAIZ / suite).is_dir(), suite


def test_nenhum_pytest_da_fatia_inteira():
    for config in FATIAS_MAPA.values():
        for cmd in config.get("testes", []):
            assert "modulos/" not in cmd, f"pytest de fatia inteira a partir da raiz: {cmd}"


def test_cada_suite_coleta_sem_erro():
    """A falha medida em 06/10 era na coleta (exit 1/2); a coleta de cada suíte tem de sair com 0."""
    for suite in _suites():
        proc = subprocess.run(
            [*comando_suite(), "--collect-only"], cwd=str(RAIZ / suite),
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        assert proc.returncode == 0, f"{suite}: exit {proc.returncode}\n{proc.stdout[-2000:]}"


def test_suites_rodam_sem_o_git_dir_do_hook(monkeypatch, tmp_path):
    """Regressão 06/10: dentro do pre-commit o GIT_DIR do hook vazava para a suíte do forge,
    cujos testes de git em tmp_path gravaram core.bare=true e [user] forge-test no .git/config real."""
    from scripts import micro_gates

    monkeypatch.setenv("GIT_DIR", str(tmp_path / "repo-real" / ".git"))
    monkeypatch.setenv("GIT_INDEX_FILE", str(tmp_path / "repo-real" / ".git" / "index"))
    proc = micro_gates._rodar(
        [sys.executable, "-c", "import os; print(os.environ.get('GIT_DIR'), os.environ.get('GIT_INDEX_FILE'))"],
        tmp_path, False,
    )
    assert proc.stdout.strip() == "None None"
