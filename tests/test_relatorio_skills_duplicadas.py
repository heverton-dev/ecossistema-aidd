# -*- coding: utf-8 -*-
"""
Ticket 11 (skills-pocock ciclo-01, D3): relatório de skills globais duplicadas.

Roda o script de verdade (subprocess) contra duas pastas temporárias (global e
projeto) e confere a tabela. O script é somente leitura: o teste reprova se
qualquer arquivo das pastas temporárias mudar, sumir ou aparecer.
"""
import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "relatorio_skills_duplicadas.py"


def _skill(base: Path, nome: str) -> None:
    d = base / nome
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text(f"---\nname: {nome}\ndescription: x\n---\n", encoding="utf-8")


def _foto(*pastas: Path) -> dict:
    return {
        str(p): hashlib.sha256(p.read_bytes()).hexdigest()
        for base in pastas
        for p in sorted(base.rglob("*"))
        if p.is_file()
    }


def _rodar(global_dir: Path, projeto_dir: Path):
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--global", str(global_dir), "--projeto", str(projeto_dir)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
    )


def _montar(tmp_path: Path):
    g = tmp_path / "global"
    p = tmp_path / "projeto"
    for nome in ("grilling", "tdd", "diagnosing-bugs", "sem-par"):
        _skill(g, nome)
    for nome in ("aidd-grill", "aidd-tdd"):
        _skill(p, nome)
    return g, p


def _linha(saida: str, upstream: str) -> str:
    linhas = [l for l in saida.splitlines() if l.startswith("|") and f"/{upstream}" in l.replace("\\", "/")]
    assert len(linhas) == 1, f"esperada 1 linha para {upstream}, achadas {linhas}"
    return linhas[0]


def test_lista_par_grilling_aidd_grill(tmp_path):
    g, p = _montar(tmp_path)
    r = _rodar(g, p)
    assert r.returncode == 0, r.stderr
    linha = _linha(r.stdout, "grilling")
    assert "aidd-grill" in linha
    assert "remover" in linha


def test_par_sem_copia_aidd_no_projeto_sugere_manter(tmp_path):
    g, p = _montar(tmp_path)
    r = _rodar(g, p)
    linha = _linha(r.stdout, "diagnosing-bugs")
    assert "aidd-diagnose" in linha
    assert "manter" in linha


def test_skill_fora_do_mapa_nao_aparece(tmp_path):
    g, p = _montar(tmp_path)
    r = _rodar(g, p)
    assert "sem-par" not in r.stdout


def test_saida_e_tabela_markdown(tmp_path):
    g, p = _montar(tmp_path)
    r = _rodar(g, p)
    assert "| Skill global | Par AIDD | Sugestão |" in r.stdout
    assert "|---|---|---|" in r.stdout


def test_somente_leitura(tmp_path):
    g, p = _montar(tmp_path)
    antes = _foto(g, p)
    r = _rodar(g, p)
    assert r.returncode == 0, r.stderr
    assert _foto(g, p) == antes


def test_pasta_global_inexistente_sai_com_erro(tmp_path):
    g, p = _montar(tmp_path)
    r = _rodar(tmp_path / "nao-existe", p)
    assert r.returncode == 1
