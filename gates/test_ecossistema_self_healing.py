# -*- coding: utf-8 -*-
"""
Testes reais do mecanismo de auto-recuperacao (self-healing) de imports do
ecossistema.py (Item PLAN-0019 self-healing-imports-python-ecossistema).

Executam o CLI real via subprocess com um sitecustomize sintetico no
PYTHONPATH que simula maquina virgem (click/dotenv indisponiveis) e um pip
fake que registra a chamada e falha sob demanda. Nao ha stub no codigo de
producao: a guarda do ecossistema.py e exercitada de ponta a ponta, com e
sem --auto-bootstrap, e a checagem de versao minima do Python.
"""

import os
import subprocess
import sys
import textwrap

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLI_PATH = os.path.join(ROOT_DIR, "ecossistema.py")

FLAG_AUTO_BOOTSTRAP = "--auto-bootstrap"

_SITECUSTOMIZE = """
    import importlib.abc
    import os
    import sys

    _base = os.path.dirname(os.path.abspath(__file__))
    _modo = os.environ.get("SELFHEAL_MODO", "bloquear")
    _marker = os.path.join(_base, "instalado.marker")

    if _modo == "python-antigo":
        sys.version_info = (3, 9, 0)
    elif _modo in ("bloquear", "liberar-apos-instalacao"):

        class _Blocker(importlib.abc.MetaPathFinder):
            def find_spec(self, name, path=None, target=None):
                if name in ("click", "dotenv"):
                    if _modo == "bloquear" or not os.path.exists(_marker):
                        raise ModuleNotFoundError("No module named %r" % name)
                return None

        sys.meta_path.insert(0, _Blocker())
"""

_PIP_MAIN = """
    import os
    import sys

    _base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(_base, "pip_args.txt"), "a", encoding="utf-8") as f:
        f.write("|".join(sys.argv[1:]) + "\\n")

    if os.environ.get("FAKE_PIP_FAIL", "") == "1":
        sys.stderr.write("[pip-fake] falha simulada\\n")
        sys.exit(1)

    with open(os.path.join(_base, "instalado.marker"), "w", encoding="utf-8") as f:
        f.write("ok\\n")
    print("Successfully installed fake-requirements-0.1.0")
"""


def _escrever(dir_base, nome_relativo, conteudo):
    caminho = os.path.join(str(dir_base), nome_relativo)
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(textwrap.dedent(conteudo))
    return caminho


def _montar_ambiente_virgem(tmp_path):
    """Cria dispositivo: sitecustomize que bloqueia click/dotenv + pip fake."""
    _escrever(tmp_path, "sitecustomize.py", _SITECUSTOMIZE)
    _escrever(tmp_path, "pip/__init__.py", "")
    _escrever(tmp_path, "pip/__main__.py", _PIP_MAIN)


def _rodar_cli(tmp_path, args, modo="bloquear", fake_pip_fail=False):
    env = os.environ.copy()
    env["PYTHONPATH"] = str(tmp_path) + os.pathsep + env.get("PYTHONPATH", "")
    env["SELFHEAL_MODO"] = modo
    env["PYTHONIOENCODING"] = "utf-8"
    if fake_pip_fail:
        env["FAKE_PIP_FAIL"] = "1"
    return subprocess.run(
        [sys.executable, CLI_PATH] + args,
        cwd=ROOT_DIR,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        timeout=120,
    )


def _ler_pip_args(tmp_path):
    caminho = os.path.join(str(tmp_path), "pip_args.txt")
    if not os.path.exists(caminho):
        return ""
    with open(caminho, "r", encoding="utf-8") as f:
        return f.read()


def test_maquina_virgem_exibe_banner_em_vez_de_traceback(tmp_path):
    """Deps indisponiveis e sem --auto-bootstrap: banner educativo, exit 1."""
    _montar_ambiente_virgem(tmp_path)

    res = _rodar_cli(tmp_path, ["help"], modo="bloquear")

    saida = res.stdout + res.stderr
    assert res.returncode == 1
    assert "Traceback" not in saida
    assert "ModuleNotFoundError" not in saida
    assert "DEPENDENCIAS AUSENTES" in res.stdout
    assert "python -m pip install -r requirements.txt" in res.stdout


def test_auto_bootstrap_instala_e_cli_prossegue(tmp_path):
    """--auto-bootstrap dispara o pip; apos instalar, o CLI continua e exit 0."""
    _montar_ambiente_virgem(tmp_path)

    res = _rodar_cli(tmp_path, [FLAG_AUTO_BOOTSTRAP, "help"], modo="liberar-apos-instalacao")

    saida = res.stdout + res.stderr
    assert "Traceback" not in saida
    assert "DEPENDENCIAS AUSENTES" in res.stdout
    assert "Instalacao concluida com sucesso" in res.stdout
    assert "Comandos dispon" in res.stdout
    assert os.path.exists(os.path.join(str(tmp_path), "instalado.marker"))
    assert res.returncode == 0

    args_pip = _ler_pip_args(tmp_path)
    assert "-r" in args_pip
    assert "requirements.txt" in args_pip


def test_auto_bootstrap_com_pip_falho_exita_sem_traceback(tmp_path):
    """Pip falha: exit 1 com mensagem, nunca traceback cru."""
    _montar_ambiente_virgem(tmp_path)

    res = _rodar_cli(
        tmp_path,
        [FLAG_AUTO_BOOTSTRAP, "help"],
        modo="liberar-apos-instalacao",
        fake_pip_fail=True,
    )

    saida = res.stdout + res.stderr
    assert res.returncode == 1
    assert "Traceback" not in saida
    assert "Instalacao falhou" in res.stdout
    assert "-r" in _ler_pip_args(tmp_path)


def test_auto_bootstrap_quando_dependencia_continua_ausente(tmp_path):
    """Pip 'instala' mas a dependencia segue indisponivel: retry falha, exit 1."""
    _montar_ambiente_virgem(tmp_path)

    res = _rodar_cli(tmp_path, [FLAG_AUTO_BOOTSTRAP, "help"], modo="bloquear")

    saida = res.stdout + res.stderr
    assert res.returncode == 1
    assert "Traceback" not in saida
    assert "ainda ausente apos a instalacao" in res.stdout
    assert "-r" in _ler_pip_args(tmp_path)


def test_python_inferior_a_3_10_exibe_banner_antes_de_imports(tmp_path):
    """Versao minima: Python 3.9 simulado exibe banner e exit 1."""
    _montar_ambiente_virgem(tmp_path)

    res = _rodar_cli(tmp_path, ["help"], modo="python-antigo")

    saida = res.stdout + res.stderr
    assert res.returncode == 1
    assert "Traceback" not in saida
    assert "PYTHON INCOMPATIVEL" in saida
    assert "Python 3.10" in saida


def test_maquina_com_dependencias_instaladas_funciona_normal(tmp_path):
    """Sem bloqueio (maquina com deps): ajuda normal e exit 0."""
    _montar_ambiente_virgem(tmp_path)

    res = _rodar_cli(tmp_path, ["help"], modo="normal")

    saida = res.stdout + res.stderr
    assert "Traceback" not in saida
    assert "DEPENDENCIAS AUSENTES" not in saida
    assert "Comandos dispon" in res.stdout
    assert res.returncode == 0