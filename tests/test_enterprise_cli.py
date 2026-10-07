# -*- coding: utf-8 -*-
"""
Teste da CLI deterministica de aidd-enterprise (Ticket 2 / D4).
Exige:
- exit 1 em parametros faltantes, entrada nao tratada ou fallback sem
  implementacao local (pacote modulos/03-plataforma-e-entrega/blindagem-enterprise/aidd-enterprise ausente).
- Subcomandos inject e audit com argumentos tipo e nome.
- Tipos de componente: skill, rule, mcp, spec, config, hook, agent.
- Roteamento direto para modulos Python locais (sem prompt de LLM).
"""

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
CLI_PATH = ROOT_DIR / ".agents" / "skills" / "aidd-enterprise" / "scripts" / "cli.py"

TIPOS_COMPONENTES = ["skill", "rule", "mcp", "spec", "config", "hook", "agent"]


def carregar_cli_enterprise():
    spec = importlib.util.spec_from_file_location("aidd_enterprise_skill_cli", str(CLI_PATH))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_import_cli():
    cli = carregar_cli_enterprise()
    assert hasattr(cli, "main")
    assert callable(cli.main)


def test_sem_subcomando_retorna_exit_1():
    """Parametro faltante: nenhum subcomando -> exit 1."""
    cli = carregar_cli_enterprise()
    assert cli.main([]) == 1


def test_subcomando_desconhecido_retorna_exit_1():
    """Entrada nao tratada: subcomando inexistente -> exit 1 (nao 2)."""
    cli = carregar_cli_enterprise()
    assert cli.main(["__comando_invalido__"]) == 1


def test_inject_sem_nome_retorna_exit_1():
    """Parametro faltante: inject sem nome -> exit 1."""
    cli = carregar_cli_enterprise()
    assert cli.main(["inject", "skill"]) == 1


def test_inject_tipo_invalido_retorna_exit_1():
    """Entrada nao tratada: tipo fora de skill/rule/mcp/spec/config/hook/agent -> exit 1."""
    cli = carregar_cli_enterprise()
    for tipo_invalido in ["arquivo", "componente", ""]:
        assert cli.main(["inject", tipo_invalido, "qualquer"]) == 1


def test_tipos_de_componente_aceitos():
    """Os 7 tipos de componente sao aceitos pelo parser de inject."""
    cli = carregar_cli_enterprise()
    registrado = {}

    def runner_falso(argumentos):
        registrado["args"] = list(argumentos)
        return 0

    cli.executar_script_local = runner_falso
    for tipo in TIPOS_COMPONENTES:
        assert cli.main(["inject", tipo, "meu-componente"]) == 0
        assert registrado["args"][0:3] == ["inject", tipo, "meu-componente"]


def test_help_retorna_exit_0():
    """Entrada tratada: --help sai com exit 0."""
    cli = carregar_cli_enterprise()
    assert cli.main(["--help"]) == 0


def test_fallback_sem_implementacao_retorna_exit_1(monkeypatch):
    """Fallback: implementacao local ausente -> exit 1 (nunca sucesso silencioso)."""
    cli = carregar_cli_enterprise()

    def sem_implementacao(argumentos):
        raise RuntimeError("pacote local modulos/03-plataforma-e-entrega/blindagem-enterprise/aidd-enterprise nao encontrado")

    monkeypatch.setattr(cli, "executar_script_local", sem_implementacao)
    assert cli.main(["inject", "skill", "auth"]) == 1
    assert cli.main(["audit", "."]) == 1


def test_roteamento_inject_para_modulo_python_local(monkeypatch):
    """inject roteia argumentos ao modulo Python local (sem prompt de LLM)."""
    cli = carregar_cli_enterprise()
    registrado = {}

    def runner_falso(argumentos):
        registrado["args"] = list(argumentos)
        return 0

    monkeypatch.setattr(cli, "executar_script_local", runner_falso)
    assert cli.main(["inject", "mcp", "servidor-x", "--dir", "."]) == 0
    assert registrado["args"] == ["inject", "mcp", "servidor-x", "--dir", "."]


def test_roteamento_audit_para_modulo_python_local(monkeypatch):
    """audit roteia argumentos ao modulo Python local (sem prompt de LLM)."""
    cli = carregar_cli_enterprise()
    registrado = {}

    def runner_falso(argumentos):
        registrado["args"] = list(argumentos)
        return 0

    monkeypatch.setattr(cli, "executar_script_local", runner_falso)
    assert cli.main(["audit", "."]) == 0
    assert registrado["args"] == ["audit", "--dir", "."]


def test_conecta_ao_pacote_local_do_repositorio():
    """A CLI aponta para o pacote local modulos/03-plataforma-e-entrega/blindagem-enterprise/aidd-enterprise (conexao deterministica)."""
    cli = carregar_cli_enterprise()
    assert cli.raiz_pacote_local() is not None
    assert (cli.raiz_pacote_local() / "scripts" / "aidd.py").is_file()


def test_execucao_real_do_fallback_sem_pacote(tmp_path):
    """End-to-end: sem pacote local, o subprocesso termina com exit 1."""
    cli = carregar_cli_enterprise()
    assert cli.raiz_pacote_local() is not None

    script = tmp_path / "cli_sem_pacote.py"
    script.write_text(
        (
            "import importlib.util, sys\n"
            f"spec = importlib.util.spec_from_file_location('cli', r'{CLI_PATH}')\n"
            "mod = importlib.util.module_from_spec(spec)\n"
            "spec.loader.exec_module(mod)\n"
            "mod.raiz_pacote_local = lambda: None\n"
            "sys.exit(mod.main(['inject', 'skill', 'auth']))\n"
        ),
        encoding="utf-8",
    )
    res = subprocess.run([sys.executable, str(script)], capture_output=True, text=True)
    assert res.returncode == 1, f"fallback sem implementacao deve terminar com exit 1 (obtido {res.returncode})"
