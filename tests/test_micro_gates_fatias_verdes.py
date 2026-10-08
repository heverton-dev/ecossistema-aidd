# -*- coding: utf-8 -*-
"""Ticket 16 (ciclo-03 VSA): micro-gates por subfatia, só com prefixos de modulos/.

Antecipado no Bloco 2: o comando antigo (pytest da fatia inteira a partir da raiz)
quebrava na coleta e barrava qualquer commit em modulos/. Bloco 6: um comando por
subfatia (só a ferramenta tocada roda), cada um com --rootdir e conftest próprios.
"""

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from scripts.micro_gates import FATIAS_MAPA, comando_suite, mapear_fatias_afetadas  # noqa: E402

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


def test_um_comando_por_subfatia_com_prefixo_da_propria_ferramenta():
    """Commit no pure não pode rodar open e freedom junto (eram 3 suítes por fatia)."""
    for fatia, config in FATIAS_MAPA.items():
        suites = config.get("suites", [])
        if not suites:
            continue
        assert len(suites) == 1, f"{fatia}: {len(suites)} suítes num comando só"
        assert config["prefixo"] == [suites[0] + "/"], f"{fatia}: prefixo {config['prefixo']}"


def test_arquivo_numa_ferramenta_dispara_so_a_subfatia_dela():
    for suite in _suites():
        afetadas = mapear_fatias_afetadas([f"{suite}/qualquer.py"])
        assert len(afetadas) == 1, f"{suite}: {afetadas}"
        assert FATIAS_MAPA[afetadas.pop()]["suites"] == [suite]


def test_cada_suite_tem_rootdir_e_conftest_proprios():
    """Sem pytest.ini próprio a raiz do pytest subia até o repositório e carregava a config
    e o conftest.py da raiz (planner, open, ops); sem conftest a limpeza do GIT_DIR do hook
    dependia só do ambiente do chamador (freedom, planner, open, ops)."""
    assert "--rootdir=." in comando_suite()
    for suite in _suites():
        pasta = RAIZ / suite
        assert (pasta / "pytest.ini").is_file(), f"{suite}: sem pytest.ini"
        conftests = [pasta / "conftest.py", pasta / "tests" / "conftest.py"]
        assert any(c.is_file() for c in conftests), f"{suite}: sem conftest.py"


def test_nenhum_pytest_da_fatia_inteira():
    for config in FATIAS_MAPA.values():
        for cmd in config.get("testes", []):
            assert "modulos/" not in cmd, f"pytest de fatia inteira a partir da raiz: {cmd}"


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


# DoD 6 (cada comando de fatia sai com 0) não roda mais aqui: rodar as 8 suítes dentro da
# bateria tests/ estourou o teto de 900 s do G_TESTES_REAIS (audit de 08/10). A prova agora
# é o pre-commit (micro-gates das fatias tocadas) e as suítes por ferramenta no G_TESTES_REAIS.
