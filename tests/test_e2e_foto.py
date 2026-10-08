# -*- coding: utf-8 -*-
"""Testes do Ticket 2 (D12): scripts/e2e_foto.py — foto E2E repetível e comparação automática.

TDD Red/Green:
  1. Fluxo que quebra MAIS CEDO que a base -> comparar exit 1.
  2. Vazamento novo fora da pasta do projeto -> comparar exit 1.
  3. Ciclo novo idêntico à base -> comparar exit 0 + COMPARACAO-E2E.md gravado.
  4. Quarteto com menos rotas respondendo -> exit 1; exit_code pior -> exit 1.
  5. Métricas de ciclo (duplicatas, tempo de gate, tokens, órfãos do inventário)
     piores -> exit 1 cada uma (prova que cada métrica é comparada de verdade).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "e2e_foto.py"

FLUXOS = ("fluxo-01-pure", "fluxo-02-open", "fluxo-03-freedom")

QUARTETO_NAO = {"api": "não (etapa master não alcançada)", "webhook": "não",
                "mcp": "não", "docs": "não"}
QUARTETO_SIM = {"api": "sim", "webhook": "sim", "mcp": "sim", "docs": "sim"}


def _resultado(fluxo: str, exit_code: int = 1, quebrou_em: str = "builder",
               quarteto: dict | None = None, vazamentos: dict | None = None,
               tokens: str = "não mensurável") -> dict:
    return {
        "fluxo": fluxo,
        "comando": f"ecossistema.py run-fluxo --fluxo {fluxo}",
        "cwd": "C:\\worktree-fake",
        "exit_code": exit_code,
        "duracao_s": 1.0,
        "quebrou_em": quebrou_em,
        "erro": [],
        "quarteto": quarteto if quarteto is not None else dict(QUARTETO_NAO),
        "arquivos_gerados": 100,
        "tokens": tokens,
        "vazamentos_fora_da_pasta": vazamentos if vazamentos is not None else {},
    }


def _escrever_ciclo(raiz: Path, nome: str, resultados: dict,
                    metricas: dict | None = None) -> Path:
    ciclo = raiz / nome
    ciclo.mkdir(parents=True, exist_ok=True)
    for pasta, dados in resultados.items():
        alvo = ciclo / pasta
        alvo.mkdir(parents=True, exist_ok=True)
        (alvo / "RESULTADO-E2E.json").write_text(
            json.dumps(dados, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")
    if metricas is not None:
        (ciclo / "METRICAS-CICLO.json").write_text(
            json.dumps(metricas, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")
    return ciclo


def _ciclo_padrao(raiz: Path, nome: str, **fluxo_kwargs) -> Path:
    resultados = {p: _resultado(p, **fluxo_kwargs) for p in FLUXOS}
    return _escrever_ciclo(raiz, nome, resultados)


def _comparar(base: Path, novo: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "comparar",
         "--base", str(base), "--novo", str(novo)],
        cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8", errors="replace",
    )


# ---------------------------------------------------------------------------
# 1. Fluxo que quebra mais cedo que a base -> exit 1
# ---------------------------------------------------------------------------
def test_comparar_reprova_quando_fluxo_quebra_mais_cedo(tmp_path):
    base = _ciclo_padrao(tmp_path, "ciclo-01")  # todos quebram em builder
    novo = _ciclo_padrao(tmp_path, "ciclo-02")
    alvo = novo / "fluxo-01-pure" / "RESULTADO-E2E.json"
    dados = json.loads(alvo.read_text(encoding="utf-8"))
    dados["quebrou_em"] = "planner"  # quebrou ANTES de builder
    alvo.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8", newline="\n")

    proc = _comparar(base, novo)

    assert proc.returncode == 1, f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
    md = novo / "COMPARACAO-E2E.md"
    assert md.exists()
    texto = md.read_text(encoding="utf-8")
    assert "quebrou_em" in texto and "planner" in texto


# ---------------------------------------------------------------------------
# 2. Vazamento novo fora da pasta -> exit 1
# ---------------------------------------------------------------------------
def test_comparar_reprova_vazamento_novo(tmp_path):
    base = _ciclo_padrao(tmp_path, "ciclo-01")
    novo = _ciclo_padrao(tmp_path, "ciclo-02")
    alvo = novo / "fluxo-02-open" / "RESULTADO-E2E.json"
    dados = json.loads(alvo.read_text(encoding="utf-8"))
    dados["vazamentos_fora_da_pasta"] = {
        "worktree": ["modulos/02-triade-motores/fluxo-01-pure/core/aidd-pure/scripts/.aidd/cache/_llm_request_abc.json"],
        "main": ["secoes/arquivo_escrito_fora_da_pasta.json"],
    }
    alvo.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8", newline="\n")

    proc = _comparar(base, novo)

    assert proc.returncode == 1, f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
    texto = (novo / "COMPARACAO-E2E.md").read_text(encoding="utf-8")
    assert "vazamento" in texto.lower()


# ---------------------------------------------------------------------------
# 3. Ciclo novo igual à base -> exit 0 + relatório gravado
# ---------------------------------------------------------------------------
def test_comparar_passa_quando_ciclos_sao_iguais(tmp_path):
    base = _ciclo_padrao(tmp_path, "ciclo-01")
    novo = _ciclo_padrao(tmp_path, "ciclo-02")

    proc = _comparar(base, novo)

    assert proc.returncode == 0, f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
    md = novo / "COMPARACAO-E2E.md"
    assert md.exists()
    texto = md.read_text(encoding="utf-8")
    assert "nenhuma métrica piorou" in texto.lower()
    assert "| SIM |" not in texto


# ---------------------------------------------------------------------------
# 4. exit_code pior que a base -> exit 1
# ---------------------------------------------------------------------------
def test_comparar_reprova_exit_code_pior(tmp_path):
    base = _escrever_ciclo(tmp_path, "ciclo-01",
                           {p: _resultado(p, exit_code=0, quebrou_em=None) for p in FLUXOS})
    novo = _ciclo_padrao(tmp_path, "ciclo-02")  # exit 1, quebrou em builder

    proc = _comparar(base, novo)

    assert proc.returncode == 1, f"stdout={proc.stdout!r} stderr={proc.stderr!r}"


# ---------------------------------------------------------------------------
# 5. Quarteto com menos rotas respondendo -> exit 1
# ---------------------------------------------------------------------------
def test_comparar_reprova_quarteto_pior(tmp_path):
    quarteto_metade = {"api": "sim", "webhook": "não", "mcp": "não", "docs": "não"}
    base = _escrever_ciclo(
        tmp_path, "ciclo-01",
        {p: _resultado(p, exit_code=0, quebrou_em=None, quarteto=QUARTETO_SIM) for p in FLUXOS})
    novo = _escrever_ciclo(
        tmp_path, "ciclo-02",
        {p: _resultado(p, exit_code=0, quebrou_em=None, quarteto=quarteto_metade) for p in FLUXOS})

    proc = _comparar(base, novo)

    assert proc.returncode == 1, f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
    texto = (novo / "COMPARACAO-E2E.md").read_text(encoding="utf-8")
    assert "quarteto" in texto.lower()


# ---------------------------------------------------------------------------
# 6. Métricas de ciclo piores (uma por vez) -> exit 1
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("metrica", ["duplicatas", "tempo_gate_s", "tokens", "orfaos_inventario"])
def test_comparar_reprova_metrica_de_ciclo_pior(tmp_path, metrica):
    base_metricas = {"duplicatas": 10, "tempo_gate_s": 100, "tokens": 50,
                     "orfaos_inventario": 0}
    novo_metricas = dict(base_metricas)
    novo_metricas[metrica] = base_metricas[metrica] + 1
    base = _escrever_ciclo(tmp_path, "ciclo-01", {}, metricas=base_metricas)
    novo = _escrever_ciclo(tmp_path, "ciclo-02", {}, metricas=novo_metricas)

    proc = _comparar(base, novo)

    assert proc.returncode == 1, f"metrica={metrica} stdout={proc.stdout!r} stderr={proc.stderr!r}"
    texto = (novo / "COMPARACAO-E2E.md").read_text(encoding="utf-8")
    assert metrica in texto


# ---------------------------------------------------------------------------
# 7. Métricas de ciclo iguais (ou ausentes no novo) -> exit 0
# ---------------------------------------------------------------------------
def test_comparar_passa_com_metricas_de_ciclo_iguais(tmp_path):
    metricas = {"duplicatas": 10, "tempo_gate_s": 100, "tokens": 50,
                "orfaos_inventario": 0}
    base = _escrever_ciclo(tmp_path, "ciclo-01", {}, metricas=metricas)
    novo = _escrever_ciclo(tmp_path, "ciclo-02", {}, metricas=metricas)

    proc = _comparar(base, novo)

    assert proc.returncode == 0, f"stdout={proc.stdout!r} stderr={proc.stderr!r}"


# ---------------------------------------------------------------------------
# 8. CLI: os dois subcomandos respondem --help com exit 0
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("subcomando", ["rodar", "comparar"])
def test_cli_aceita_subcomando(subcomando):
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), subcomando, "--help"],
        cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert proc.returncode == 0, f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
    assert subcomando in proc.stdout


# ---------------------------------------------------------------------------
# 9. Base real (ciclo-01) comparada contra ela mesma -> exit 0
# ---------------------------------------------------------------------------
def test_comparar_ciclo01_contra_ele_mesmo(tmp_path):
    sys.path.insert(0, str(ROOT / "scripts"))
    import e2e_foto
    raiz = e2e_foto.raiz_padrao() / "ciclo-01"
    if not (raiz / "fluxo-01-pure" / "RESULTADO-E2E.json").exists():
        pytest.skip(f"ciclo-01 real não encontrado em {raiz}")
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "comparar",
         "--base", str(raiz), "--novo", str(raiz),
         "--saida", str(tmp_path / "COMPARACAO-E2E.md")],
        cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert proc.returncode == 0, f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
    assert (tmp_path / "COMPARACAO-E2E.md").exists()


def _repo_git(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    for args in (["init", "-q", "-b", "main"], ["config", "user.email", "t@t"], ["config", "user.name", "t"],
                 ["config", "core.hooksPath", "/dev/null"]):
        subprocess.run(["git", *args], cwd=repo, check=True)
    (repo / "README.md").write_text("x", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "base"], cwd=repo, check=True)
    return repo


def test_rodar_remove_a_worktree_e_a_branch_que_criou(tmp_path, monkeypatch):
    # 2026-10-02: cada E2E deixava worktrees_e2e-ciclo-NN + branch aidd/e2e-ciclo-NN para trás.
    sys.path.insert(0, str(ROOT / "scripts"))
    import e2e_foto
    repo = _repo_git(tmp_path)
    raiz = tmp_path / "TESTES"
    monkeypatch.setattr(e2e_foto, "repo_raiz", lambda: repo)
    for nome in ("rodar_fluxo", "rodar_continuacao", "gravar_quarteto_no_resultado", "checar_quarteto"):
        monkeypatch.setattr(e2e_foto, nome, lambda *a, **k: None)
    monkeypatch.setattr(e2e_foto, "resolver_origem", lambda *a, **k: raiz)

    assert e2e_foto.main(["rodar", "--ciclo", "auto", "--raiz", str(raiz)]) == 0

    assert not (tmp_path / "worktrees_e2e-ciclo-01").exists()
    branches = subprocess.run(["git", "branch", "--list", "aidd/e2e-*"], cwd=repo,
                              capture_output=True, text=True).stdout
    assert branches.strip() == ""
    worktrees = subprocess.run(["git", "worktree", "list"], cwd=repo, capture_output=True, text=True).stdout
    assert len(worktrees.strip().splitlines()) == 1
