# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — TESTE DO ORQUESTRADOR 4F: GATE POR FASE + BRANCH DO CICLO
=============================================================================
Regressões (2026-09-24):
  1. Cada fase era commitada com --no-verify sem NENHUM gate: saída não
     conferida entrava no histórico.
  2. Cada fase era mergeada direto na branch atual (normalmente main) antes da
     aprovação humana ("Join Barrier" só no fim, com tudo já dentro).

Regras:
  - Cada fase declara 'gate_fase'; ausente -> exit 1 antes de chamar o agente.
  - gate_fase roda na worktree ANTES do commit; exit != 0 -> pipeline para,
    nada é commitado, fases seguintes não rodam.
  - As fases acumulam numa branch própria (audit/<pipeline_id>); a branch
    atual não muda durante a execução.
  - No fim roda 'gate_final' (bateria completa) uma única vez; só se passar o
    ciclo fica aprovável.
  - Merge na branch atual só com --aprovar (ação humana), e só se o topo da
    branch do ciclo for exatamente o commit aprovado pelo gate_final.
=============================================================================
"""

import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))

import orquestrador_4f  # noqa: E402

OK = f'"{sys.executable}" -c "import sys; sys.exit(0)"'
FALHA = f'"{sys.executable}" -c "import sys; sys.exit(1)"'


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=True).stdout.strip()


@pytest.fixture
def repo(tmp_path, monkeypatch):
    r = tmp_path / "repo"
    r.mkdir()
    _git(r, "init", "-q", "-b", "main")
    _git(r, "config", "user.email", "t@t")
    _git(r, "config", "user.name", "t")
    _git(r, "config", "core.hooksPath", "/dev/null")
    (r / "p.txt").write_text("prompt", encoding="utf-8")
    (r / "README.md").write_text("base", encoding="utf-8")
    _git(r, "add", "-A")
    _git(r, "commit", "-q", "-m", "base")
    monkeypatch.chdir(r)

    chamadas = []

    def agente_falso(cmd, cwd=None, input_data=None, expected_handoff=None, titulo=None):
        chamadas.append(expected_handoff.name)
        expected_handoff.parent.mkdir(parents=True, exist_ok=True)
        expected_handoff.write_text(f"saida {expected_handoff.name}", encoding="utf-8")
        return True

    monkeypatch.setattr(orquestrador_4f, "run_cmd_tty", agente_falso)
    return SimpleNamespace(path=r, chamadas=chamadas)


def _manifesto(repo: Path, fases: list, gate_final: str = OK) -> Path:
    m = repo / "m.json"
    m.write_text(json.dumps({"pipeline_id": "aud-x-ciclo-01", "target_tool": "x", "ciclo": "ciclo-01",
                             "gate_final": gate_final, "fases": fases}), encoding="utf-8")
    return m


def _fase(nome: str, saida: str, gate: str = OK) -> dict:
    f = {"nome": nome, "comando_terminal": "agente", "input_prompt": "p.txt", "output_handoff": saida}
    if gate is not None:
        f["gate_fase"] = gate
    return f


def _rodar(monkeypatch, *args: str) -> int:
    monkeypatch.setattr(sys, "argv", ["orquestrador_4f.py", *args])
    try:
        orquestrador_4f.main()
    except SystemExit as e:
        return e.code or 0
    return 0


def test_fases_acumulam_na_branch_do_ciclo_e_main_nao_muda(repo, monkeypatch):
    base = _git(repo.path, "rev-parse", "main")
    m = _manifesto(repo.path, [_fase("Fase_1_Inspetor", "out/a.md"), _fase("Fase_2_Arquiteto", "out/b.md")])

    assert _rodar(monkeypatch, "--manifest", str(m)) == 0
    assert _git(repo.path, "rev-parse", "main") == base
    assert not (repo.path / "out").exists()
    assert _git(repo.path, "show", "audit/aud-x-ciclo-01:out/a.md") == "saida a.md"
    assert _git(repo.path, "show", "audit/aud-x-ciclo-01:out/b.md") == "saida b.md"


def test_gate_da_fase_reprova_para_tudo_sem_commitar(repo, monkeypatch):
    m = _manifesto(repo.path, [_fase("Fase_1_Inspetor", "out/a.md", gate=FALHA), _fase("Fase_2_Arquiteto", "out/b.md")])

    assert _rodar(monkeypatch, "--manifest", str(m)) == 1
    assert repo.chamadas == ["a.md"]
    arquivos = _git(repo.path, "ls-tree", "-r", "--name-only", "audit/aud-x-ciclo-01")
    assert "out/a.md" not in arquivos.split()


def test_fase_sem_gate_reprova_antes_de_chamar_agente(repo, monkeypatch):
    m = _manifesto(repo.path, [_fase("Fase_1_Inspetor", "out/a.md", gate=None)])

    assert _rodar(monkeypatch, "--manifest", str(m)) == 1
    assert repo.chamadas == []


def test_gate_final_reprova_e_ciclo_nao_fica_aprovavel(repo, monkeypatch):
    base = _git(repo.path, "rev-parse", "main")
    m = _manifesto(repo.path, [_fase("Fase_1_Inspetor", "out/a.md")], gate_final=FALHA)

    assert _rodar(monkeypatch, "--manifest", str(m)) == 1
    assert _rodar(monkeypatch, "--manifest", str(m), "--aprovar") == 1
    assert _git(repo.path, "rev-parse", "main") == base


def test_aprovar_mergeia_na_branch_atual_e_remove_branch_do_ciclo(repo, monkeypatch):
    m = _manifesto(repo.path, [_fase("Fase_1_Inspetor", "out/a.md")])
    assert _rodar(monkeypatch, "--manifest", str(m)) == 0

    assert _rodar(monkeypatch, "--manifest", str(m), "--aprovar") == 0
    assert (repo.path / "out" / "a.md").read_text(encoding="utf-8") == "saida a.md"
    assert "audit/aud-x-ciclo-01" not in _git(repo.path, "branch", "--list")


def test_aprovar_sem_execucao_aprovada_reprova(repo, monkeypatch):
    m = _manifesto(repo.path, [_fase("Fase_1_Inspetor", "out/a.md")])
    assert _rodar(monkeypatch, "--manifest", str(m), "--aprovar") == 1


def test_aprovar_reprova_se_branch_mudou_depois_do_gate_final(repo, monkeypatch):
    m = _manifesto(repo.path, [_fase("Fase_1_Inspetor", "out/a.md")])
    assert _rodar(monkeypatch, "--manifest", str(m)) == 0

    wt = repo.path.parent / "wt_mexe"
    _git(repo.path, "worktree", "add", str(wt), "audit/aud-x-ciclo-01")
    (wt / "extra.txt").write_text("sem gate", encoding="utf-8")
    _git(wt, "add", "-A")
    _git(wt, "commit", "-q", "-m", "mudanca sem gate")
    _git(repo.path, "worktree", "remove", "--force", str(wt))

    assert _rodar(monkeypatch, "--manifest", str(m), "--aprovar") == 1
    assert not (repo.path / "extra.txt").exists()


def test_preparo_do_gate_final_copia_so_config_local_ignorada(repo, monkeypatch, tmp_path):
    (repo.path / ".gitignore").write_text(".local/mcp.json\n", encoding="utf-8")
    (repo.path / "versionado.json").write_text("main", encoding="utf-8")
    _git(repo.path, "add", "-A")
    _git(repo.path, "commit", "-q", "-m", "configs")
    (repo.path / ".local").mkdir()
    (repo.path / ".local" / "mcp.json").write_text('{"mcpServers": {}}', encoding="utf-8")
    monkeypatch.setattr(orquestrador_4f, "configs_mcp_locais",
                        lambda: [Path(".local/mcp.json"), Path("versionado.json"), Path("ausente.json")])

    wt = tmp_path / "wt_final"
    _git(repo.path, "worktree", "add", "-q", "--detach", str(wt), "HEAD")
    (wt / "versionado.json").write_text("ciclo", encoding="utf-8")
    orquestrador_4f.preparar_worktree_gate_final(wt, repo.path)

    assert (wt / ".local" / "mcp.json").read_text(encoding="utf-8") == '{"mcpServers": {}}'
    assert (wt / "versionado.json").read_text(encoding="utf-8") == "ciclo"  # versionado nunca é sobrescrito
    assert not (wt / "ausente.json").exists()


def test_retomada_com_fases_commitadas_roda_so_o_gate_final(repo, monkeypatch, capsys):
    # Pipeline parou antes de aprovar (gate_final reprovou / última fase concluída à mão).
    m = _manifesto(repo.path, [_fase("Fase_1_Inspetor", "out/a.md")], gate_final=FALHA)
    assert _rodar(monkeypatch, "--manifest", str(m)) == 1
    repo.chamadas.clear()

    m = _manifesto(repo.path, [_fase("Fase_1_Inspetor", "out/a.md")], gate_final=OK)
    assert _rodar(monkeypatch, "--manifest", str(m)) == 0
    assert repo.chamadas == []  # nenhum agente de novo
    assert "RETOMADA" in capsys.readouterr().out
    assert _rodar(monkeypatch, "--manifest", str(m), "--aprovar") == 0


def test_rerodar_antes_de_aprovar_nao_repete_fases(repo, monkeypatch, capsys):
    m = _manifesto(repo.path, [_fase("Fase_1_Inspetor", "out/a.md")])
    assert _rodar(monkeypatch, "--manifest", str(m)) == 0
    repo.chamadas.clear()

    assert _rodar(monkeypatch, "--manifest", str(m)) == 0
    assert repo.chamadas == []
    assert "NADA A FAZER" in capsys.readouterr().out
