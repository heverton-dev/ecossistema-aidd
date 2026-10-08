# -*- coding: utf-8 -*-
"""
aidd-visual-maps ciclo-01, Ticket 13 (D2 / D10): CLI unificada e ordem do pipeline garantida.

Antes, regenerar os mapas era uma sequência de scripts soltos (catálogo, cada mapa, índice,
livro) que dependia de quem rodava lembrar a ordem; `python ecossistema.py visual-maps`
nem existia. Agora a skill tem cli.py com catalogo, mapa <tipo>, gerar e check:
  - check: frescor do catálogo, --check de cada mapa e do livro, exit 1 no primeiro desvio;
  - gerar: catálogo -> mapas -> índice -> livro, numa worktree efêmera, promovendo só os
    arquivos das pastas dos mapas (escopo do Ticket 10) via gravar_lote.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _repo_mapas import commitar, copiar_repo, rodar  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CLI = "componentes/compartilhado/skills/aidd-visual-maps/scripts/cli.py"
CATALOGO = "docs/auditoria/mapa-pecas/catalogo-pecas.json"
SCRIPT_NOVO = "scripts/peca_nova_do_teste_cli.py"


def _estagios(pasta: Path) -> list[tuple[str, str]]:
    arquivo = pasta / "aidd-visual-maps.jsonl"
    linhas = arquivo.read_text(encoding="utf-8").splitlines() if arquivo.is_file() else []
    return [(m["estagio"], m["tipo"]) for m in map(json.loads, filter(str.strip, linhas))]


def test_visual_maps_check_no_repositorio_real():
    for comando in ("visual-maps", "aidd-visual-maps"):
        proc = rodar(ROOT, "ecossistema.py", comando, "check")
        assert proc.returncode == 0, f"{comando}: {proc.stdout}\n{proc.stderr}"
        assert "[OK]" in proc.stdout


@pytest.fixture(scope="module")
def repo(tmp_path_factory):
    raiz = copiar_repo(tmp_path_factory.mktemp("repo_cli"))
    proc = rodar(raiz, "scripts/catalogo_pecas.py")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    commitar(raiz, ".", mensagem="fixture com catálogo da cópia")
    # Peça nova, não versionada: o catálogo commitado fica velho e a worktree efêmera
    # tem de enxergar a árvore de trabalho, não só o HEAD.
    (raiz / SCRIPT_NOVO).write_text('"""Peça nova que o catálogo ainda não conhece."""\n', encoding="utf-8")
    return raiz


def test_check_reprova_catalogo_velho(repo):
    proc = rodar(repo, CLI, "check")
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "[DESATUALIZADO]" in proc.stdout and "catálogo" in proc.stdout


def test_gerar_segue_a_ordem_e_deixa_tudo_em_dia(repo, tmp_path):
    medicoes = tmp_path / "medicoes"
    antes = (repo / "AGENTS.md").read_bytes()

    proc = rodar(repo, CLI, "gerar", env={"AIDD_MEDICOES_DIR": str(medicoes)})
    assert proc.returncode == 0, proc.stdout + proc.stderr

    estagios = _estagios(medicoes)
    nomes = [e for e, _ in estagios]
    assert nomes[0] == "catalogo", estagios
    assert nomes[-1] == "livro", estagios
    mapas = [t for e, t in estagios if e == "mapa"]
    assert mapas and mapas[-1] == "indice" and "indice" not in mapas[:-1], estagios
    assert nomes.index("livro") > max(i for i, e in enumerate(nomes) if e == "mapa")

    assert "peca_nova_do_teste_cli" in (repo / CATALOGO).read_text(encoding="utf-8")
    assert (repo / "AGENTS.md").read_bytes() == antes
    worktrees = subprocess.run(["git", "worktree", "list", "--porcelain"], cwd=repo,
                               capture_output=True, text=True, check=True).stdout
    assert worktrees.count("worktree ") == 1, f"worktree efêmera não foi removida:\n{worktrees}"

    check = rodar(repo, CLI, "check")
    assert check.returncode == 0, check.stdout + check.stderr


def test_subcomandos_delegam_aos_scripts(repo, tmp_path):
    saida = tmp_path / "leis.html"
    proc = rodar(repo, CLI, "mapa", "leis", "--saida", str(saida))
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert saida.is_file()

    fora = rodar(repo, CLI, "catalogo", "--saida", "AGENTS.md")
    assert fora.returncode == 1 and "[ERRO]" in fora.stdout

    desconhecido = rodar(repo, CLI, "nao-existe")
    assert desconhecido.returncode != 0
