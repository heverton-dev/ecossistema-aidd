# -*- coding: utf-8 -*-
"""
Teste de Isolamento de Raio de Impacto para aidd-enterprise (Ticket 1 / D3).
Exige:
- Confineamento estrito de escrita nos componentes autorizados (allowlist) e
  na worktree efemera.
- Exit 1 (SandboxViolationError) quando a ferramenta escreve fora dos caminhos
  permitidos, na raiz do repositorio ou fora da worktree efemera.
"""

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
SKILL_SCRIPTS = ROOT_DIR / ".agents" / "skills" / "aidd-enterprise" / "scripts"
ISOLAMENTO_PATH = SKILL_SCRIPTS / "isolamento.py"

CAMINHOS_PERMITIDOS = [
    ".agents/skills/aidd-enterprise",
    "gates",
    "docs/auditoria/aidd-enterprise",
]


def carregar_isolamento_enterprise():
    spec = importlib.util.spec_from_file_location("aidd_enterprise_isolamento", str(ISOLAMENTO_PATH))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_import_isolamento():
    """Importa o modulo de isolamento de aidd-enterprise."""
    ent_mod = carregar_isolamento_enterprise()
    assert hasattr(ent_mod, "validar_caminho_escrita")
    assert hasattr(ent_mod, "SandboxViolationError")
    assert hasattr(ent_mod, "escrever_com_isolamento")


def test_escrita_dentro_de_componentes_listados_ou_worktree_e_permitida(tmp_path):
    """Permite escrita apenas em componentes da allowlist e na worktree efemera."""
    ent_mod = carregar_isolamento_enterprise()
    validar_caminho_escrita = ent_mod.validar_caminho_escrita

    repo_alvo = tmp_path / "alvo"
    worktree_dir = tmp_path / "worktrees_enterprise-ciclo-01"
    worktree_dir.mkdir()

    # Permitido: componente listado (skill)
    skill_ok = repo_alvo / ".agents" / "skills" / "aidd-enterprise" / "scripts" / "isolamento.py"
    assert (
        validar_caminho_escrita(
            skill_ok,
            repo_root=repo_alvo,
            caminhos_permitidos=CAMINHOS_PERMITIDOS,
            worktree_dir=worktree_dir,
        )
        is True
    )

    # Permitido: componente listado (gate)
    gate_ok = repo_alvo / "gates" / "G_aidd_enterprise.py"
    assert (
        validar_caminho_escrita(
            gate_ok,
            repo_root=repo_alvo,
            caminhos_permitidos=CAMINHOS_PERMITIDOS,
            worktree_dir=worktree_dir,
        )
        is True
    )

    # Permitido: qualquer caminho dentro da worktree efemera isolada
    wt_ok = worktree_dir / "qualquer" / "arquivo.py"
    assert (
        validar_caminho_escrita(
            wt_ok,
            repo_root=repo_alvo,
            caminhos_permitidos=CAMINHOS_PERMITIDOS,
            worktree_dir=worktree_dir,
        )
        is True
    )


def test_escrita_em_diretorio_nao_listado_falha(tmp_path):
    """Exit 1: diretorio fora da allowlist (mesmo dentro do repo) deve falhar."""
    ent_mod = carregar_isolamento_enterprise()
    validar_caminho_escrita = ent_mod.validar_caminho_escrita
    SandboxViolationError = ent_mod.SandboxViolationError

    repo_alvo = tmp_path / "alvo"
    nao_listado = repo_alvo / "docs" / "relatorios" / "infiltrado.py"

    with pytest.raises(SandboxViolationError):
        validar_caminho_escrita(
            nao_listado,
            repo_root=repo_alvo,
            caminhos_permitidos=CAMINHOS_PERMITIDOS,
            worktree_dir=None,
        )


def test_escrita_na_raiz_do_repositorio_falha(tmp_path):
    """Exit 1: escrita solta na raiz do repositorio nao pertence a nenhum componente."""
    ent_mod = carregar_isolamento_enterprise()
    validar_caminho_escrita = ent_mod.validar_caminho_escrita
    SandboxViolationError = ent_mod.SandboxViolationError

    repo_alvo = tmp_path / "alvo"

    with pytest.raises(SandboxViolationError):
        validar_caminho_escrita(
            repo_alvo / "arquivo_solto_na_raiz.py",
            repo_root=repo_alvo,
            caminhos_permitidos=CAMINHOS_PERMITIDOS,
            worktree_dir=None,
        )


def test_escrita_fora_do_repo_e_fora_da_worktree_falha(tmp_path):
    """Exit 1: escrita fora do repo alvo, fora da worktree e via traversal."""
    ent_mod = carregar_isolamento_enterprise()
    validar_caminho_escrita = ent_mod.validar_caminho_escrita
    SandboxViolationError = ent_mod.SandboxViolationError

    repo_alvo = tmp_path / "alvo"
    worktree_dir = tmp_path / "worktrees_enterprise-ciclo-01"
    worktree_dir.mkdir()
    fora = tmp_path / "fora_do_escopo"
    fora.mkdir()

    # PROIBIDO: diretorio externo ao repo e a worktree
    with pytest.raises(SandboxViolationError):
        validar_caminho_escrita(
            fora / "infiltrado.py",
            repo_root=repo_alvo,
            caminhos_permitidos=CAMINHOS_PERMITIDOS,
            worktree_dir=worktree_dir,
        )

    # PROIBIDO: traversal `..` saindo do repositorio alvo
    with pytest.raises(SandboxViolationError):
        validar_caminho_escrita(
            repo_alvo / ".." / "fora_do_escopo" / "escape.py",
            repo_root=repo_alvo,
            caminhos_permitidos=CAMINHOS_PERMITIDOS,
            worktree_dir=worktree_dir,
        )


def test_guard_de_escrita_bloqueia_fora_da_allowlist(tmp_path):
    """Guard de escrita: alvo nao listado nao cria arquivo."""
    ent_mod = carregar_isolamento_enterprise()
    escrever_com_isolamento = ent_mod.escrever_com_isolamento
    SandboxViolationError = ent_mod.SandboxViolationError

    repo_alvo = tmp_path / "alvo"

    with pytest.raises(SandboxViolationError):
        escrever_com_isolamento(
            repo_root=repo_alvo,
            alvo_relativo="docs/relatorios/escape.py",
            conteudo="# ESCAPE\n",
            caminhos_permitidos=CAMINHOS_PERMITIDOS,
            worktree_dir=None,
        )
    assert not (repo_alvo / "docs" / "relatorios" / "escape.py").exists()


def test_guard_de_escrita_escreve_no_componente_listado(tmp_path):
    """Guard de escrita: componente listado recebe o arquivo."""
    ent_mod = carregar_isolamento_enterprise()
    escrever_com_isolamento = ent_mod.escrever_com_isolamento

    repo_alvo = tmp_path / "alvo"

    destino = escrever_com_isolamento(
        repo_root=repo_alvo,
        alvo_relativo=".agents/skills/aidd-enterprise/scripts/novo.py",
        conteudo="# ENTERPRISE\n",
        caminhos_permitidos=CAMINHOS_PERMITIDOS,
        worktree_dir=None,
    )
    assert destino.exists()
    assert destino.read_text(encoding="utf-8") == "# ENTERPRISE\n"


def test_falha_de_isolamento_provoca_exit_code_1(tmp_path):
    """End-to-end: subprocesso escrevendo fora da allowlist termina com exit 1."""
    ent_mod = carregar_isolamento_enterprise()
    repo_alvo = tmp_path / "alvo"
    repo_alvo.mkdir()

    script = tmp_path / "motor_enterprise.py"
    script.write_text(
        (
            "import importlib.util, sys\n"
            f"spec = importlib.util.spec_from_file_location('isol', r'{ISOLAMENTO_PATH}')\n"
            "mod = importlib.util.module_from_spec(spec)\n"
            "spec.loader.exec_module(mod)\n"
            "try:\n"
            "    mod.escrever_com_isolamento(\n"
            f"        repo_root=r'{repo_alvo}',\n"
            "        alvo_relativo='docs/relatorios/fuga.py',\n"
            "        conteudo='FUGA',\n"
            f"        caminhos_permitidos={CAMINHOS_PERMITIDOS!r},\n"
            "        worktree_dir=None,\n"
            "    )\n"
            "    sys.exit(0)\n"
            "except mod.SandboxViolationError:\n"
            "    sys.exit(1)\n"
        ),
        encoding="utf-8",
    )

    res = subprocess.run([sys.executable, str(script)], capture_output=True, text=True)
    assert res.returncode == 1, f"Escrever fora da allowlist deve terminar com exit 1 (obtido {res.returncode})"
    assert not (repo_alvo / "docs" / "relatorios" / "fuga.py").exists()
