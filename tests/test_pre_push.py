# -*- coding: utf-8 -*-
"""
Ticket 8 do ciclo agilidade-gates: push com código exige bateria completa verde.

Com o commit do dia a dia em modo rápido, o último portão antes do remoto é o
pre-push: código só sobe se a bateria completa passou para aquele conteúdo
(registro por árvore, gravado pelo gate_final). Push só de documentação passa direto.
"""

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import medir_gates  # noqa: E402


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=True).stdout.strip()


@pytest.fixture
def repo(tmp_path):
    remoto = tmp_path / "remoto.git"
    _git(tmp_path, "init", "-q", "--bare", str(remoto))
    r = tmp_path / "repo"
    r.mkdir()
    _git(r, "init", "-q", "-b", "main")
    _git(r, "config", "user.email", "t@t")
    _git(r, "config", "user.name", "t")
    _git(r, "config", "core.hooksPath", "/dev/null")
    (r / "README.md").write_text("base\n", encoding="utf-8")
    _git(r, "add", "-A")
    _git(r, "commit", "-q", "-m", "base")
    _git(r, "remote", "add", "origin", str(remoto))
    _git(r, "push", "-q", "origin", "main")
    return r


def _commit(repo: Path, caminho: str, texto: str) -> str:
    arquivo = repo / caminho
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    arquivo.write_text(texto, encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", f"muda {caminho}")
    return _git(repo, "rev-parse", "HEAD")


def _linha(repo: Path, sha: str) -> list:
    return [f"refs/heads/main {sha} refs/heads/main {_git(repo, 'rev-parse', 'origin/main')}"]


def test_push_de_codigo_sem_registro_roda_bateria_e_bloqueia_se_reprovar(repo):
    sha = _commit(repo, "app.py", "x = 1\n")
    chamadas = []
    codigo = medir_gates.verificar_push(_linha(repo, sha), repo,
                                        rodar_bateria=lambda raiz: chamadas.append(raiz) or 1, avisar=lambda m: None)
    assert codigo == 1 and len(chamadas) == 1
    assert not medir_gates.registro_verde(repo, medir_gates.arvore_de(repo, sha)).exists()


def test_push_de_codigo_sem_registro_com_bateria_verde_grava_registro(repo):
    sha = _commit(repo, "app.py", "x = 1\n")
    codigo = medir_gates.verificar_push(_linha(repo, sha), repo, rodar_bateria=lambda raiz: 0, avisar=lambda m: None)
    assert codigo == 0
    assert medir_gates.registro_verde(repo, medir_gates.arvore_de(repo, sha)).is_file()


def test_push_so_de_documentacao_nao_roda_bateria(repo):
    _commit(repo, "docs/guia.md", "texto\n")
    sha = _commit(repo, "secoes/historico.json", "{}\n")
    codigo = medir_gates.verificar_push(_linha(repo, sha), repo,
                                        rodar_bateria=lambda raiz: pytest.fail("não devia rodar bateria"),
                                        avisar=lambda m: None)
    assert codigo == 0


def test_registro_por_arvore_vale_para_o_merge_do_aprovar(repo):
    _git(repo, "checkout", "-q", "-b", "audit/ciclo")
    _commit(repo, "app.py", "x = 1\n")
    medir_gates.registrar_bateria_verde(repo, "audit/ciclo")  # o que o gate_final grava
    _git(repo, "checkout", "-q", "main")
    _git(repo, "merge", "-q", "--no-ff", "-m", "aprova", "audit/ciclo")  # SHA novo, mesma árvore
    sha = _git(repo, "rev-parse", "HEAD")

    codigo = medir_gates.verificar_push(_linha(repo, sha), repo,
                                        rodar_bateria=lambda raiz: pytest.fail("não devia repetir a bateria"),
                                        avisar=lambda m: None)
    assert codigo == 0


def test_hook_pre_push_esta_versionado_e_chama_a_verificacao():
    hook = ROOT / ".githooks" / "pre-push"
    assert "medir_gates.py --verificar-push" in hook.read_text(encoding="utf-8")
    modo = subprocess.run(["git", "ls-files", "-s", ".githooks/pre-push"], cwd=ROOT,
                          capture_output=True, text=True).stdout.split()[0]
    assert modo == "100755"
