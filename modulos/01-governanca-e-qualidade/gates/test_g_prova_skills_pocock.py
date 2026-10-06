# -*- coding: utf-8 -*-
"""
Teste do G_PROVA_SKILLS_POCOCK (skills-pocock ciclo-01, Ticket 13 / D13).

Usa só artefatos salvos em tests/fixtures/skills_pocock/artefatos/ (modo
--artefatos): nenhum modelo é chamado aqui. Prova que cada checagem morde:
artefato bom -> exit 0; trocar UM artefato por um ruim -> exit 1 citando a skill.

Rótulo honesto: os artefatos bons/ruins foram escritos à mão. A prova de que
um agente real segue as skills é a execução real do gate (sem --artefatos),
registrada no RELATORIO-CONSTRUTOR.md do ciclo.
"""
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
GATE = ROOT / "gates" / "G_PROVA_SKILLS_POCOCK.py"
FIXTURES = ROOT / "tests" / "fixtures" / "skills_pocock"
BOM = FIXTURES / "artefatos" / "bom"
RUIM = FIXTURES / "artefatos" / "ruim"
SKILLS = ["aidd-diagnose", "aidd-tickets", "aidd-grill", "aidd-tdd"]


def rodar_gate(pasta: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(GATE), "--artefatos", str(pasta)],
        cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8",
        errors="replace", timeout=300,
    )


def copia_boa_com(tmp_path: Path, skill: str, conteudo: str) -> Path:
    pasta = tmp_path / "artefatos"
    shutil.copytree(BOM, pasta)
    (pasta / f"{skill}.md").write_text(conteudo, encoding="utf-8")
    return pasta


def test_artefatos_bons_passam():
    res = rodar_gate(BOM)
    assert res.returncode == 0, res.stdout + res.stderr


@pytest.mark.parametrize("skill", SKILLS)
def test_bite_artefato_ruim_de_cada_skill(tmp_path, skill):
    pasta = copia_boa_com(tmp_path, skill, (RUIM / f"{skill}.md").read_text(encoding="utf-8"))
    res = rodar_gate(pasta)
    assert res.returncode == 1, res.stdout
    assert f"[{skill}] REPROVADO" in res.stdout


def _diagnose_com_comando(comando: str) -> str:
    texto = (BOM / "aidd-diagnose.md").read_text(encoding="utf-8")
    inicio = texto.index("- **Comando**: `")
    fim = texto.index("`", inicio + len("- **Comando**: `"))
    return texto[:inicio] + f"- **Comando**: `{comando}`" + texto[fim + 1:]


@pytest.mark.parametrize("comando, motivo", [
    ('python -c "pass"', "não fica vermelho"),
    ('python -c "import sys; sys.exit(1)"', "continua vermelho depois da correção"),
    ("dir", "só comandos python"),
])
def test_bite_comando_de_reproducao_falso(tmp_path, comando, motivo):
    pasta = copia_boa_com(tmp_path, "aidd-diagnose", _diagnose_com_comando(comando))
    res = rodar_gate(pasta)
    assert res.returncode == 1, res.stdout
    assert motivo in res.stdout


def _diagnose_com_hipoteses_em_tabela(linhas: int) -> str:
    texto = (BOM / "aidd-diagnose.md").read_text(encoding="utf-8")
    inicio = texto.index("1. `media()`")
    fim = texto.index("HIPOTESES ATIVAS:")
    tabela = "| # | Hipótese | Refutada se |\n|---|---|---|\n" + "".join(
        f"| **H{n}** | hipótese {n} | observação {n} |\n" for n in range(1, linhas + 1)
    )
    return texto[:inicio] + tabela + "\n" + texto[fim:]


def test_hipoteses_em_tabela_contam(tmp_path):
    pasta = copia_boa_com(tmp_path, "aidd-diagnose", _diagnose_com_hipoteses_em_tabela(3))
    res = rodar_gate(pasta)
    assert res.returncode == 0, res.stdout


def test_bite_tabela_com_duas_hipoteses(tmp_path):
    pasta = copia_boa_com(tmp_path, "aidd-diagnose", _diagnose_com_hipoteses_em_tabela(2))
    res = rodar_gate(pasta)
    assert res.returncode == 1, res.stdout
    assert "só 2 hipótese(s)" in res.stdout


def test_recomendacao_com_motivo_sem_rotulo_conta(tmp_path):
    grill = (
        "### Consolidated Assumptions\n\n"
        "1. Senha mínima: 8 caracteres, porque é o padrão comum.\n"
        "2. E-mail sem diferença de maiúsculas, because users type both.\n"
        "3. IDs sequenciais. *Razão:* clareza.\n"
    )
    pasta = copia_boa_com(tmp_path, "aidd-grill", grill)
    res = rodar_gate(pasta)
    assert res.returncode == 0, res.stdout


def test_bite_artefato_ausente(tmp_path):
    pasta = tmp_path / "artefatos"
    shutil.copytree(BOM, pasta)
    (pasta / "aidd-tdd.md").unlink()
    res = rodar_gate(pasta)
    assert res.returncode == 1
    assert "[aidd-tdd] REPROVADO" in res.stdout


def test_fixture_do_projeto_continua_com_o_bug():
    """O gate depende do bug plantado: se alguém 'corrigir' a fixture, a prova some."""
    codigo = (FIXTURES / "projeto_bug" / "calc.py").read_text(encoding="utf-8")
    assert "len(valores) - 1" in codigo
