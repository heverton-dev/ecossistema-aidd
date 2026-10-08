# -*- coding: utf-8 -*-
"""
Ticket 18 (ciclo-03, D15): skills com dono único e `components sync` lendo as fatias.

Origens de skill: componentes/compartilhado/skills (escopo compartilhado) e
<ferramenta>/skills/ de cada ferramenta do MAPA-FATIAS (um escopo por ferramenta).
O sync de uma fatia grava as cópias de harness dentro da própria ferramenta;
`--ferramenta <nome>` limita a gravação àquela fatia (lazy_skills_scope).
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

import gestor_componentes  # noqa: E402
import lazy_skills_scope  # noqa: E402

MANIFESTO_REAL = json.loads(
    (RAIZ / "modulos/04-nucleo-compartilhado/contracts/manifesto_harnesses.json").read_text(encoding="utf-8")
)
PASTAS_HARNESS = {".agents", ".claude", ".cursor", ".gemini", ".mimocode", ".opencode", ".codebuddy", ".skills"}


def _skill(pasta: Path, nome: str) -> None:
    (pasta / nome).mkdir(parents=True)
    (pasta / nome / "SKILL.md").write_text(f"---\nname: {nome}\n---\n# {nome}\n", encoding="utf-8")


@pytest.fixture
def arvore(tmp_path, monkeypatch):
    """Ecossistema sintético: 1 skill compartilhada e 2 ferramentas, uma com skill própria."""
    contratos = tmp_path / "modulos/04-nucleo-compartilhado/contracts"
    contratos.mkdir(parents=True)
    (contratos / "dependencias_externas.json").write_text("{}", encoding="utf-8")
    (contratos / "MAPA-FATIAS.json").write_text(json.dumps({"fatias": {
        "fatia-x": {"caminho": "modulos/02/fatia-x", "ferramentas": ["core/aidd-x"]},
        "fatia-y": {"caminho": "modulos/03/fatia-y", "ferramentas": ["aidd-y"]},
    }}), encoding="utf-8")
    _skill(tmp_path / "componentes/compartilhado/skills", "skill-comp")
    _skill(tmp_path / "modulos/02/fatia-x/core/aidd-x/skills", "skill-x")
    _skill(tmp_path / "modulos/03/fatia-y/aidd-y/skills", "skill-y")
    monkeypatch.setattr(gestor_componentes, "ROOT_DIR", str(tmp_path))
    monkeypatch.setattr(gestor_componentes, "COMPONENTES_DIR", str(tmp_path / "componentes"))
    monkeypatch.setattr(gestor_componentes, "carregar_manifesto", lambda: json.loads(json.dumps(MANIFESTO_REAL)))
    return tmp_path


def test_nenhuma_skill_com_o_mesmo_nome_no_compartilhado_e_nas_fatias():
    compartilhadas = {p.name for p in (RAIZ / "componentes/compartilhado/skills").iterdir() if p.is_dir()}
    nas_fatias = set()
    for pasta in lazy_skills_scope.pastas_das_ferramentas(RAIZ).values():
        nas_fatias.update(p.name for p in lazy_skills_scope.skills_da_ferramenta(pasta))
    assert compartilhadas & nas_fatias == set()


def test_pastas_das_ferramentas_vem_do_mapa_fatias(arvore):
    pastas = lazy_skills_scope.pastas_das_ferramentas(arvore)
    assert pastas == {
        "aidd-x": arvore / "modulos/02/fatia-x/core/aidd-x",
        "aidd-y": arvore / "modulos/03/fatia-y/aidd-y",
    }
    assert [p.name for p in lazy_skills_scope.skills_da_ferramenta(pastas["aidd-x"])] == ["skill-x"]


def test_sync_materializa_skill_que_so_existe_na_fatia(arvore):
    gestor_componentes.sync("skill")
    ferramenta = arvore / "modulos/02/fatia-x/core/aidd-x"
    assert (ferramenta / ".claude/skills/skill-x/SKILL.md").is_file()
    assert (ferramenta / ".skills/skill-x/SKILL.md").is_file()
    manifesto_gemini = ferramenta / ".gemini/extensions/skill-x/gemini-extension.json"
    assert b"\r\n" not in manifesto_gemini.read_bytes(), "manifesto extra gravado com CRLF vira drift no git"
    # a skill da fatia não vaza para a raiz, e a compartilhada não entra na ferramenta
    assert not (arvore / ".claude/skills/skill-x").exists()
    assert not (ferramenta / ".claude/skills/skill-comp").exists()
    assert (arvore / ".claude/skills/skill-comp/SKILL.md").is_file()


def test_sync_de_uma_fatia_grava_so_a_fatia(arvore):
    gestor_componentes.sync("skill", ferramenta="aidd-x")
    assert (arvore / "modulos/02/fatia-x/core/aidd-x/.claude/skills/skill-x/SKILL.md").is_file()
    assert not (arvore / "modulos/03/fatia-y/aidd-y/.claude").exists()
    assert not (arvore / ".claude").exists()


def test_sync_nunca_trata_a_fonte_da_fatia_como_destino(arvore):
    fonte = arvore / "modulos/02/fatia-x/core/aidd-x/skills"
    manifesto = gestor_componentes.carregar_manifesto()
    destinos = gestor_componentes._resolver_destinos(manifesto, "skill", "aidd-x", "skill-x")
    assert str(fonte / "skill-x") not in {os.path.normpath(d) for d in destinos}


def test_verify_acusa_copia_de_fatia_divergente(arvore):
    gestor_componentes.sync("skill")
    assert gestor_componentes.verify("skill")[1] == []
    copia = arvore / "modulos/03/fatia-y/aidd-y/.claude/skills/skill-y/SKILL.md"
    copia.write_text("editado a mao\n", encoding="utf-8")
    problemas = gestor_componentes.verify("skill", ferramenta="aidd-y")[1]
    assert any("skill/aidd-y/skill-y" in p for p in problemas)


def test_repo_real_tem_escopo_de_skill_para_cada_ferramenta_com_skills():
    manifesto = gestor_componentes.carregar_manifesto()
    escopos = set(gestor_componentes._escopos_do_tipo(manifesto, "skill"))
    for nome, pasta in lazy_skills_scope.pastas_das_ferramentas(RAIZ).items():
        if lazy_skills_scope.skills_da_ferramenta(pasta):
            assert nome in escopos, f"components sync ignora as skills de {nome}"


def test_components_verify_real_sai_0():
    env = {k: v for k, v in os.environ.items() if k not in ("GIT_DIR", "GIT_INDEX_FILE")}
    res = subprocess.run(
        [sys.executable, "ecossistema.py", "components", "verify", "--tipo", "todos"],
        cwd=RAIZ, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env,
    )
    assert res.returncode == 0, res.stdout[-2000:] + res.stderr[-2000:]
