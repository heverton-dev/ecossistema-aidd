# -*- coding: utf-8 -*-
"""
Teste de Isolamento de Raio de Impacto para aidd-forge (Ticket 1 / D3 / DoD 2).
Exige:
- Confineamento estrito de escrita no diretorio alvo (repo_root) ou na worktree isolada.
- Exit 1 (SandboxViolationError) quando a ferramenta escreve fora do diretorio alvo
  ou fora da worktree efemera (inclusive via traversal `..`).
- Guard de escrita que protege as fronteiras do repositorio alvo.
"""

import importlib.util
import subprocess
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
SKILL_SCRIPTS = ROOT_DIR / ".agents" / "skills" / "aidd-forge" / "scripts"


def carregar_isolamento_forge():
    caminho = SKILL_SCRIPTS / "isolamento.py"
    spec = importlib.util.spec_from_file_location("aidd_forge_isolamento", str(caminho))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_import_isolamento():
    """Importa o modulo de isolamento de aidd-forge."""
    forge_mod = carregar_isolamento_forge()
    assert hasattr(forge_mod, "validar_caminho_escrita")
    assert hasattr(forge_mod, "SandboxViolationError")
    assert hasattr(forge_mod, "escrever_com_isolamento")


def test_escrita_dentro_do_diretorio_alvo_ou_worktree_e_permitida(tmp_path):
    """Permite escrita dentro do repositorio alvo e dentro da worktree isolada."""
    forge_mod = carregar_isolamento_forge()
    validar_caminho_escrita = forge_mod.validar_caminho_escrita

    repo_alvo = tmp_path / "alvo"
    repo_alvo.mkdir()
    worktree_dir = tmp_path / "worktrees_forge-ciclo-01"
    worktree_dir.mkdir()

    # Permitido: dentro do diretorio alvo
    alvo_ok = repo_alvo / "gates" / "G_novo.py"
    assert validar_caminho_escrita(alvo_ok, repo_root=repo_alvo, worktree_dir=worktree_dir) is True

    # Permitido: dentro da worktree efemera
    wt_ok = worktree_dir / "src" / "forge.py"
    assert validar_caminho_escrita(wt_ok, repo_root=repo_alvo, worktree_dir=worktree_dir) is True


def test_escrita_fora_do_diretorio_alvo_e_fora_da_worktree_falha(tmp_path):
    """Exit 1: escrita fora do diretorio alvo e fora da worktree isolada deve falhar."""
    forge_mod = carregar_isolamento_forge()
    validar_caminho_escrita = forge_mod.validar_caminho_escrita
    SandboxViolationError = forge_mod.SandboxViolationError

    repo_alvo = tmp_path / "alvo"
    repo_alvo.mkdir()
    worktree_dir = tmp_path / "worktrees_forge-ciclo-01"
    worktree_dir.mkdir()
    fora = tmp_path / "fora_do_escopo"
    fora.mkdir()

    # PROIBIDO: diretorio externo ao alvo e a worktree
    with pytest.raises(SandboxViolationError):
        validar_caminho_escrita(fora / "infiltrado.py", repo_root=repo_alvo, worktree_dir=worktree_dir)

    # PROIBIDO: traversal `..` saindo do repositorio alvo
    com_traversal = repo_alvo / ".." / "fora_do_escopo" / "escape.py"
    with pytest.raises(SandboxViolationError):
        validar_caminho_escrita(com_traversal, repo_root=repo_alvo, worktree_dir=worktree_dir)

    # PROIBIDO: sem worktree, escrita fora do diretorio alvo continua bloqueada
    with pytest.raises(SandboxViolationError):
        validar_caminho_escrita(fora / "outro.py", repo_root=repo_alvo, worktree_dir=None)


def test_guard_de_escrita_bloqueia_saida_do_repositorio_alvo(tmp_path):
    """Guard de escrita: alvo com traversal `..` nao cria arquivo fora do repositorio."""
    forge_mod = carregar_isolamento_forge()
    escrever_com_isolamento = forge_mod.escrever_com_isolamento
    SandboxViolationError = forge_mod.SandboxViolationError

    repo_alvo = tmp_path / "alvo"
    repo_alvo.mkdir()
    fora = tmp_path / "fora_do_escopo"
    fora.mkdir()

    alvo_malicioso = "../fora_do_escopo/escape.py"
    with pytest.raises(SandboxViolationError):
        escrever_com_isolamento(
            repo_root=repo_alvo,
            alvo_relativo=alvo_malicioso,
            conteudo="# ESCAPE\n",
            worktree_dir=None,
        )
    assert not (fora / "escape.py").exists(), "Arquivo nao pode ser criado fora do diretorio alvo"


def test_guard_de_escrita_escreve_com_sucesso_no_escopo(tmp_path):
    """Guard de escrita: escrita valida dentro do diretorio alvo cria o arquivo."""
    forge_mod = carregar_isolamento_forge()
    escrever_com_isolamento = forge_mod.escrever_com_isolamento

    repo_alvo = tmp_path / "alvo"
    repo_alvo.mkdir()

    destino = escrever_com_isolamento(
        repo_root=repo_alvo,
        alvo_relativo="gates/G_teste.py",
        conteudo="# PORTAO\n",
        worktree_dir=None,
    )
    assert destino.exists()
    assert destino.read_text(encoding="utf-8") == "# PORTAO\n"


def test_falha_de_isolamento_provoca_exit_code_1(tmp_path):
    """Cenario end-to-end: subprocesso que tenta escrever fora do escopo termina com exit 1."""
    forge_mod = carregar_isolamento_forge()
    repo_alvo = tmp_path / "alvo"
    repo_alvo.mkdir()
    fora = tmp_path / "fora_do_escopo"
    fora.mkdir()

    script = tmp_path / "motor_forge.py"
    script.write_text(
        (
            "import importlib.util, sys\n"
            f"spec = importlib.util.spec_from_file_location('isol', r'{SKILL_SCRIPTS / 'isolamento.py'}')\n"
            "mod = importlib.util.module_from_spec(spec)\n"
            "spec.loader.exec_module(mod)\n"
            "try:\n"
            "    mod.escrever_com_isolamento(\n"
            f"        repo_root=r'{repo_alvo}',\n"
            f"        alvo_relativo=r'{'../fora_do_escopo/fuga.py'}',\n"
            "        conteudo='FUGA',\n"
            "        worktree_dir=None,\n"
            "    )\n"
            "    sys.exit(0)\n"
            "except mod.SandboxViolationError:\n"
            "    sys.exit(1)\n"
        ),
        encoding="utf-8",
    )

    res = subprocess.run([sys_executable(), str(script)], capture_output=True, text=True)
    assert res.returncode == 1, f"Escrever fora do escopo deve terminar com exit 1 (obtido {res.returncode})"
    assert not (fora / "fuga.py").exists()


def sys_executable():
    import sys

    return sys.executable
