#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ticket 11 (ciclo-03 VSA, D13 / DoD 4): G_MODULO_FRONTEIRA prova que morde.

Repo temporario com duas fatias (MAPA-FATIAS.json proprio). Cada acoplamento
plantado fora de interface.py tem de ser acusado:
  1. sys.path.insert/append apontando para a outra fatia;
  2. caminho literal para dentro da outra fatia (string e Path/os.path.join);
  3. referencia a tools/aidd-* (pasta extinta no Ticket 5);
  4. import de pacote que so existe na outra fatia.
Em bloqueio (padrao desde o Ticket 20) sai com 1; em aviso, 0. Allowlist datada perdoa, mas so pode
diminuir: entrada a mais que o teto, entrada sem data/motivo ou entrada morta
reprovam.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

GATES_DIR = Path(__file__).resolve().parent
GATE = GATES_DIR / "G_MODULO_FRONTEIRA.py"
CONTRATOS_REL = Path("modulos") / "04-nucleo-compartilhado" / "contracts"
ALLOWLIST_REL = CONTRATOS_REL / "allowlist_modulo_fronteira.json"

VARIAVEIS_DO_HOOK = ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR", "GIT_PREFIX")


def _escrever(caminho: Path, texto: str) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(texto, encoding="utf-8")


def _rodar(raiz: Path, *args: str, modo_env: str | None = None) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if k not in VARIAVEIS_DO_HOOK}
    env.pop("AIDD_MODULO_FRONTEIRA_MODO", None)
    if modo_env:
        env["AIDD_MODULO_FRONTEIRA_MODO"] = modo_env
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run([sys.executable, str(GATE), "--raiz", str(raiz), *args],
                          capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)


def _allowlist(raiz: Path, entradas: list, teto: int | None = None) -> None:
    _escrever(raiz / ALLOWLIST_REL, json.dumps(
        {"teto": len(entradas) if teto is None else teto, "entradas": entradas}, indent=2))


@pytest.fixture
def repo(tmp_path):
    """Duas fatias: alfa (ferramenta aidd-alfa, pacote alfa_pkg) e beta (aidd-beta, beta_pkg)."""
    raiz = tmp_path / "repo"
    _escrever(raiz / CONTRATOS_REL / "MAPA-FATIAS.json", json.dumps({
        "raizes_import": ["", "src", "scripts"],
        "caixas_de_layout": ["src", "scripts", "tests"],
        "fatias": {
            "fatia-alfa": {"caminho": "modulos/01-x/fatia-alfa", "ferramentas": ["aidd-alfa"]},
            "fatia-beta": {"caminho": "modulos/02-y/fatia-beta", "ferramentas": ["aidd-beta"]},
        },
    }))
    alfa = raiz / "modulos/01-x/fatia-alfa"
    beta = raiz / "modulos/02-y/fatia-beta"
    _escrever(alfa / "aidd-alfa/alfa_pkg/__init__.py", "")
    _escrever(beta / "aidd-beta/beta_pkg/__init__.py", "VALOR = 1\n")
    _escrever(beta / "interface.py", "from pathlib import Path\nRAIZ_BETA = Path(__file__).parent\n__all__ = ['RAIZ_BETA']\n")
    _escrever(alfa / "interface.py", "__all__ = []\n")
    _escrever(alfa / "aidd-alfa/alfa_pkg/limpo.py", "import os\nX = os.path.join('a', 'b')\n")
    _allowlist(raiz, [])
    return raiz


def _plantar(repo: Path, nome: str, codigo: str) -> str:
    rel = f"modulos/01-x/fatia-alfa/aidd-alfa/alfa_pkg/{nome}.py"
    _escrever(repo / rel, codigo)
    return rel


def test_repo_limpo_passa_em_bloqueio(repo):
    proc = _rodar(repo, "--modo", "bloqueio")
    assert proc.returncode == 0, proc.stdout + proc.stderr


CASOS = {
    "sys_path": ("import sys, os\nsys.path.insert(0, os.path.join(R, 'modulos', '02-y', 'fatia-beta', 'aidd-beta'))\n",
                 "sys.path"),
    "caminho_literal": ("CAMINHO = 'modulos/02-y/fatia-beta/aidd-beta/beta_pkg/x.py'\n", "caminho"),
    "path_join": ("from pathlib import Path\nP = Path(R) / 'modulos' / '02-y' / 'fatia-beta'\n", "caminho"),
    "tools": ("ANTIGO = 'tools/aidd-beta/scripts/x.py'\n", "tools"),
    "import_pacote": ("from beta_pkg import VALOR\n", "import"),
}


@pytest.mark.parametrize("caso", sorted(CASOS))
def test_cada_acoplamento_plantado_e_acusado(repo, caso):
    codigo, tipo = CASOS[caso]
    rel = _plantar(repo, caso, codigo)
    proc = _rodar(repo, "--modo", "bloqueio")
    assert proc.returncode == 1, f"{caso} nao mordeu:\n{proc.stdout}"
    assert rel in proc.stdout and f"[{tipo}]" in proc.stdout, proc.stdout
    padrao = _rodar(repo)  # padrao: bloqueio (Ticket 20)
    assert padrao.returncode == 1 and "modo bloqueio" in padrao.stdout, padrao.stdout
    aviso = _rodar(repo, "--modo", "aviso")
    assert aviso.returncode == 0 and rel in aviso.stdout, aviso.stdout


def test_interface_py_pode_apontar_para_a_propria_fatia_e_e_unico_ponto_cruzado(repo):
    _escrever(repo / "modulos/01-x/fatia-alfa/interface.py",
              "import sys\nfrom pathlib import Path\n"
              "sys.path.insert(0, str(Path(__file__).parent / 'aidd-alfa'))\n__all__ = ['sys']\n")
    assert _rodar(repo, "--modo", "bloqueio").returncode == 0


def test_docstring_e_comentario_nao_contam(repo):
    _plantar(repo, "doc", '"""Gera arquivos para modulos/02-y/fatia-beta (so texto)."""\n# tools/aidd-beta antigo\nX = 1\n')
    assert _rodar(repo, "--modo", "bloqueio").returncode == 0


def test_allowlist_datada_perdoa(repo):
    rel = _plantar(repo, "acoplado", "from beta_pkg import VALOR\n")
    _allowlist(repo, [{"arquivo": rel, "tipo": "import", "alvo": "fatia-beta",
                       "data": "2026-10-07", "motivo": "teste"}])
    proc = _rodar(repo, "--modo", "bloqueio")
    assert proc.returncode == 0, proc.stdout


def test_allowlist_que_cresce_alem_do_teto_reprova(repo):
    rel = _plantar(repo, "acoplado", "from beta_pkg import VALOR\n")
    entrada = {"arquivo": rel, "tipo": "import", "alvo": "fatia-beta", "data": "2026-10-07", "motivo": "teste"}
    _allowlist(repo, [entrada], teto=0)
    proc = _rodar(repo)  # vale ate em aviso: allowlist so pode diminuir
    assert proc.returncode == 1 and "teto" in proc.stdout, proc.stdout


def test_entrada_sem_data_ou_morta_reprova_em_bloqueio(repo):
    _allowlist(repo, [{"arquivo": "modulos/01-x/fatia-alfa/aidd-alfa/alfa_pkg/limpo.py", "tipo": "import",
                       "alvo": "fatia-beta", "data": "2026-10-07", "motivo": "nao existe mais"}])
    assert _rodar(repo, "--modo", "bloqueio").returncode == 1
    rel = _plantar(repo, "acoplado", "from beta_pkg import VALOR\n")
    _allowlist(repo, [{"arquivo": rel, "tipo": "import", "alvo": "fatia-beta", "motivo": "sem data"}])
    assert _rodar(repo, "--modo", "bloqueio").returncode == 1


def test_modo_invalido_sai_com_1(repo):
    assert _rodar(repo, modo_env="talvez").returncode == 1


def test_repo_real_em_aviso_lista_acoplamentos_e_sai_0():
    raiz_real = next(p.parent for p in GATES_DIR.parents if p.name == "modulos")
    proc = _rodar(raiz_real, "--modo", "aviso")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "[G_MODULO_FRONTEIRA] modo aviso" in proc.stdout


def test_pacote_que_tambem_existe_na_raiz_do_repo_nao_e_atribuido_a_fatia(repo):
    """`core/` da raiz do ecossistema (ex.: core.anti_lockin) não é o `core` de uma fatia."""
    _escrever(repo / "modulos/02-y/fatia-beta/aidd-beta/core/__init__.py", "")
    _escrever(repo / "core/__init__.py", "")
    _plantar(repo, "usa_raiz", "from core.anti_lockin import varredura\n")
    assert _rodar(repo, "--modo", "bloqueio").returncode == 0
