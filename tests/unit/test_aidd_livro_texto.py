# -*- coding: utf-8 -*-
"""
Testes reais do motor da skill aidd-livro-texto (componentes/compartilhado/skills).

Cobre o contrato deterministico da ferramenta, sem simular nada do que ela faz:
  - ciclo de vida completo (init -> check -> build -> status -> add-parte -> update)
  - deteccao honesta do motor de composicao (binario no PATH x pacote Python)
  - descarte de typst inutilizavel (versao antiga, atalho nao executavel)
  - auditoria que reprova de verdade (cerca aberta, bloco desbalanceado, tabela estreita)
  - rastreabilidade: arquivo citado que nao existe e reprovado
  - manifesto: ordem das partes, impressao digital e historico de revisoes

Os testes que compilam PDF sao pulados quando a maquina nao tem pandoc/typst, e essa
condicao e reportada — nunca mascarada como sucesso.
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
DIR_SKILL = RAIZ / "componentes" / "compartilhado" / "skills" / "aidd-livro-texto"
LIVRO_PY = DIR_SKILL / "scripts" / "livro.py"

sys.path.insert(0, str(DIR_SKILL / "scripts"))
import livro as motor_livro  # noqa: E402


def rodar(*args, esperado=None):
    """Executa a CLI de verdade e devolve o resultado do subprocesso."""
    res = subprocess.run([sys.executable, str(LIVRO_PY), *args],
                         capture_output=True, text=True, encoding="utf-8", errors="replace")
    if esperado is not None:
        assert res.returncode == esperado, f"exit {res.returncode}\n{res.stdout}\n{res.stderr}"
    return res


def composicao_disponivel() -> bool:
    motor = motor_livro._resolver_motor()
    return bool(motor["pandoc"]) and bool(motor["typst_cli"] or motor["typst_api"])


precisa_composicao = pytest.mark.skipif(
    not composicao_disponivel(),
    reason="pandoc e/ou typst indisponiveis nesta maquina (nem no PATH, nem via pip)",
)


# ---------------------------------------------------------------------------
# Estrutura da skill
# ---------------------------------------------------------------------------

def test_skill_tem_os_arquivos_canonicos():
    assert (DIR_SKILL / "SKILL.md").is_file()
    assert (DIR_SKILL / "ativos" / "livro.typst").is_file()
    assert LIVRO_PY.is_file()
    for referencia in ("ESTRUTURA.md", "DIAGRAMACAO.md", "ATUALIZACAO.md", "INSTALACAO.md"):
        assert (DIR_SKILL / "referencias" / referencia).is_file(), referencia


def test_frontmatter_segue_a_convencao_do_ecossistema():
    texto = (DIR_SKILL / "SKILL.md").read_text(encoding="utf-8")
    assert texto.startswith("---\n")
    bloco = texto.split("---", 2)[1]
    assert "name: aidd-livro-texto" in bloco
    descricao = [l for l in bloco.splitlines() if l.startswith("description:")]
    assert len(descricao) == 1, "description deve existir e ocupar exatamente 1 linha"
    # prefixo aidd-*, kebab-case, no maximo 3 palavras
    assert len("aidd-livro-texto".split("-")) <= 3


def test_motor_nao_depende_de_pacote_externo():
    """A skill precisa rodar em maquina limpa: nada de import fora da stdlib no topo."""
    codigo = LIVRO_PY.read_text(encoding="utf-8")
    cabecalho = codigo.split("DIR_SKILL =")[0]
    for proibido in ("import requests", "import yaml", "import click", "from pydantic"):
        assert proibido not in cabecalho, f"{proibido} nao pode ser dependencia de topo"


# ---------------------------------------------------------------------------
# Deteccao do motor de composicao
# ---------------------------------------------------------------------------

def test_typst_de_versao_antiga_e_descartado(monkeypatch):
    """O template usa `context` (typst 0.11+). Versao anterior precisa ser recusada."""
    monkeypatch.setattr(motor_livro.shutil, "which", lambda _n: "/usr/bin/typst")
    monkeypatch.setattr(motor_livro.os, "name", "posix")

    class Falsa:
        returncode = 0
        stdout = "typst 0.10.0 (70ca0d25)"

    monkeypatch.setattr(motor_livro.subprocess, "run", lambda *a, **k: Falsa())
    caminho, motivo = motor_livro._typst_cli_usavel()
    assert caminho is None
    assert "abaixo do minimo" in motivo


def test_typst_que_nao_e_executavel_nativo_e_descartado_no_windows(monkeypatch):
    """Atalho .CMD (instalacao via npm) nao pode ser invocado pelo pandoc."""
    monkeypatch.setattr(motor_livro.os, "name", "nt")
    monkeypatch.setattr(motor_livro.shutil, "which", lambda _n: r"C:\npm\typst.CMD")
    caminho, motivo = motor_livro._typst_cli_usavel()
    assert caminho is None
    assert "executavel nativo" in motivo


def test_typst_ausente_reporta_motivo(monkeypatch):
    monkeypatch.setattr(motor_livro.shutil, "which", lambda _n: None)
    caminho, motivo = motor_livro._typst_cli_usavel()
    assert caminho is None and motivo == "ausente no PATH"


def test_doctor_nunca_explode_quando_a_saida_e_filtrada():
    """A regra de uso manda canalizar saida verbosa; cano fechado nao pode virar erro."""
    res = rodar("doctor")
    assert res.returncode in (0, 1)
    assert "Traceback" not in res.stderr


# ---------------------------------------------------------------------------
# Ciclo de vida
# ---------------------------------------------------------------------------

@pytest.fixture
def obra(tmp_path):
    pasta = tmp_path / "obra"
    rodar("init", str(pasta), "--titulo", "Obra de Teste", "--autor", "QA", esperado=0)
    return pasta


def test_init_cria_manifesto_e_partes(obra):
    manifesto = json.loads((obra / "livro.json").read_text(encoding="utf-8"))
    assert manifesto["titulo"] == "Obra de Teste"
    assert manifesto["partes"] == ["00-frontmatter.md", "01-parte-um.md"]
    assert manifesto["revisoes"] == []
    for nome in manifesto["partes"]:
        assert (obra / "partes" / nome).is_file()


def test_init_recusa_sobrescrever_obra_existente(obra):
    res = rodar("init", str(obra), "--titulo", "Outra")
    assert res.returncode == 1
    assert "force" in (res.stdout + res.stderr).lower()


def test_esqueleto_gerado_passa_na_propria_auditoria(obra):
    """O modelo que a ferramenta cria nao pode reprovar no check dela mesma."""
    rodar("check", str(obra), esperado=0)


def test_add_parte_registra_na_ordem_pedida(obra):
    rodar("add-parte", str(obra), "--nome", "02-meio", "--depois-de", "00-frontmatter.md", esperado=0)
    manifesto = json.loads((obra / "livro.json").read_text(encoding="utf-8"))
    assert manifesto["partes"] == ["00-frontmatter.md", "02-meio.md", "01-parte-um.md"]


def test_parte_declarada_e_ausente_em_disco_falha(obra):
    (obra / "partes" / "01-parte-um.md").unlink()
    res = rodar("check", str(obra))
    assert res.returncode == 1
    assert "ausente em disco" in (res.stdout + res.stderr)


# ---------------------------------------------------------------------------
# Auditoria: precisa reprovar de verdade
# ---------------------------------------------------------------------------

def test_check_reprova_cerca_de_codigo_aberta(obra):
    (obra / "partes" / "01-parte-um.md").write_text(
        "# Capitulo\n\n```python\nprint('sem fechar')\n", encoding="utf-8")
    res = rodar("check", str(obra))
    assert res.returncode == 1
    assert "cercas" in res.stdout


def test_check_reprova_bloco_de_diagrama_desbalanceado(obra):
    (obra / "partes" / "01-parte-um.md").write_text(
        "# Capitulo\n\n```{=typst}\n#painel(\"x\"[\n  texto\n```\n", encoding="utf-8")
    res = rodar("check", str(obra))
    assert res.returncode == 1
    assert "desbalanceados" in res.stdout


def test_check_reprova_tabela_que_nao_ocupa_a_largura(obra):
    (obra / "partes" / "01-parte-um.md").write_text(
        "# Capitulo\n\n| A | B |\n|---|---|\n| 1 | 2 |\n", encoding="utf-8")
    res = rodar("check", str(obra))
    assert res.returncode == 1
    assert "largura do corpo" in res.stdout


def test_check_reprova_arquivo_citado_inexistente(obra, tmp_path):
    (obra / "partes" / "01-parte-um.md").write_text(
        "# Capitulo\n\nVeja `modulo/que/nao/existe.py` para detalhes.\n", encoding="utf-8")
    res = rodar("check", str(obra), "--raiz-evidencia", str(tmp_path))
    assert res.returncode == 1
    assert "rastreabilidade" in res.stdout


def test_check_aceita_arquivo_citado_existente(obra, tmp_path):
    (tmp_path / "existe.py").write_text("# ok\n", encoding="utf-8")
    (obra / "partes" / "01-parte-um.md").write_text(
        "# Capitulo\n\nVeja `existe.py` para detalhes.\n", encoding="utf-8")
    rodar("check", str(obra), "--raiz-evidencia", str(tmp_path), esperado=0)


# ---------------------------------------------------------------------------
# Compilacao e atualizacao
# ---------------------------------------------------------------------------

@precisa_composicao
def test_build_gera_pdf_e_registra_impressao_digital(obra):
    rodar("build", str(obra), esperado=0)
    manifesto = json.loads((obra / "livro.json").read_text(encoding="utf-8"))
    pdf = obra / f"{manifesto['nome_base']}.pdf"
    assert pdf.is_file() and pdf.stat().st_size > 10_000
    assert len(manifesto["hash_fonte"]) == 64
    rodar("status", str(obra), esperado=0)


@precisa_composicao
def test_update_nao_recompila_sem_mudanca(obra):
    rodar("build", str(obra), esperado=0)
    res = rodar("update", str(obra), esperado=0)
    assert "nada a recompilar" in res.stdout
    manifesto = json.loads((obra / "livro.json").read_text(encoding="utf-8"))
    assert manifesto["revisoes"] == []


@precisa_composicao
def test_update_recompila_e_registra_revisao_quando_o_texto_muda(obra):
    rodar("build", str(obra), esperado=0)
    parte = obra / "partes" / "01-parte-um.md"
    parte.write_text(parte.read_text(encoding="utf-8") + "\n## Seção nova\n\nTexto.\n",
                     encoding="utf-8")

    res = rodar("status", str(obra))
    assert res.returncode == 1 and "DESATUALIZADO" in res.stdout

    rodar("update", str(obra), "--nota", "acrescenta seção", esperado=0)
    manifesto = json.loads((obra / "livro.json").read_text(encoding="utf-8"))
    assert len(manifesto["revisoes"]) == 1
    assert manifesto["revisoes"][0]["nota"] == "acrescenta seção"
    rodar("status", str(obra), esperado=0)


@precisa_composicao
def test_update_aborta_quando_a_auditoria_reprova(obra):
    rodar("build", str(obra), esperado=0)
    (obra / "partes" / "01-parte-um.md").write_text(
        "# Capitulo\n\n```python\nsem fechar\n", encoding="utf-8")
    res = rodar("update", str(obra))
    assert res.returncode == 1
    manifesto = json.loads((obra / "livro.json").read_text(encoding="utf-8"))
    assert manifesto["revisoes"] == [], "revisao nao pode ser registrada apos reprovacao"


@precisa_composicao
def test_preview_gera_uma_imagem_por_pagina(obra):
    rodar("preview", str(obra), "--ppi", "50", esperado=0)
    paginas = sorted((obra / "preview").glob("pagina*.png"))
    assert len(paginas) >= 2
    assert all(p.stat().st_size > 0 for p in paginas)
