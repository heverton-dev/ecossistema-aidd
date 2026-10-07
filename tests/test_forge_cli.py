# -*- coding: utf-8 -*-
"""
Teste da CLI deterministica de aidd-forge (Ticket 2 / D4 / DoD 1).
Exige:
- exit 1 em parametros faltantes ou entrada nao tratada (subcomando ausente,
  subcomando desconhecido, argumentos obrigatorios ausentes).
- exit 0 para --help (entrada tratada).
- Delegacao deterministica aos scripts locais (pacote aidd_forge), sem
  interpretacao por prompt de LLM.
- ecossistema.py forge roteado para a script local da skill.
"""

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
CLI_PATH = ROOT_DIR / ".agents" / "skills" / "aidd-forge" / "scripts" / "cli.py"


def carregar_cli_forge():
    spec = importlib.util.spec_from_file_location("aidd_forge_skill_cli", str(CLI_PATH))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_import_cli():
    cli = carregar_cli_forge()
    assert hasattr(cli, "main")
    assert callable(cli.main)


def test_sem_subcomando_retorna_exit_1():
    """Parametro faltante: nenhuma subcomando -> exit 1."""
    cli = carregar_cli_forge()
    assert cli.main([]) == 1


def test_subcomando_desconhecido_retorna_exit_1():
    """Entrada nao tratada: subcomando inexistente -> exit 1 (nao 2)."""
    cli = carregar_cli_forge()
    assert cli.main(["__comando_invalido__"]) == 1


def test_argumento_obrigatorio_ausente_retorna_exit_1():
    """Parametro faltante: inject sem --descricao -> exit 1."""
    cli = carregar_cli_forge()
    assert cli.main(["inject", "skill", "minha-skill"]) == 1


def test_help_retorna_exit_0():
    """Entrada tratada: --help sai com exit 0."""
    cli = carregar_cli_forge()
    assert cli.main(["--help"]) == 0


def test_delegacao_deterministica_para_scripts_locais(monkeypatch):
    """init delega ao runner local com os argumentos recebidos (sem LLM)."""
    cli = carregar_cli_forge()
    registrado = {}

    def runner_falso(argumentos):
        registrado["args"] = list(argumentos)
        return 0

    monkeypatch.setattr(cli, "executar_script_local", runner_falso)
    assert cli.main(["init", ".", "--force"]) == 0
    assert registrado["args"] == ["init", ".", "--force"]


def test_falha_no_script_local_retorna_exit_1(monkeypatch):
    """Entrada nao tratada: runner local indisponivel/falho -> exit 1."""
    cli = carregar_cli_forge()

    def runner_falho(argumentos):
        raise RuntimeError("pacote aidd_forge indisponivel")

    monkeypatch.setattr(cli, "executar_script_local", runner_falho)
    assert cli.main(["init"]) == 1


def test_conecta_ao_pacote_local_do_repositorio():
    """A CLI aponta para o pacote local modulos/01-governanca-e-qualidade/core/aidd-forge (conexao deterministica)."""
    cli = carregar_cli_forge()
    raiz_pacote = cli.raiz_pacote_local()
    assert raiz_pacote is not None
    assert (raiz_pacote / "aidd_forge" / "cli.py").is_file()


def test_ecossistema_forge_roteado_para_script_local():
    """ecossistema.py forge usa a script local da skill (exit 1 em entrada invalida)."""
    res = subprocess.run(
        [sys.executable, str(ROOT_DIR / "ecossistema.py"), "forge", "__comando_invalido__"],
        capture_output=True,
        text=True,
        cwd=str(ROOT_DIR),
        timeout=180,
    )
    assert res.returncode == 1, (
        f"esperava exit 1 da CLI local (obtido {res.returncode}): "
        f"{(res.stdout + res.stderr)[-800:]}"
    )
