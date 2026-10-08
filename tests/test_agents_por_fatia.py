# -*- coding: utf-8 -*-
"""
Ticket 17 (ciclo-03, D14): contexto enxuto em cada fatia e subfatia.

Fatias e subfatias vêm de modulos/04-nucleo-compartilhado/contracts/MAPA-FATIAS.json
(subfatia = pasta de ferramenta da fatia). Cada uma precisa de AGENTS.md (< 400 tokens)
e README.md (< 500 tokens), medidos com a mesma régua do validador fractal.
O AGENTS.md raiz despacha para o AGENTS.md de cada fatia, e o validador exige os dois arquivos.
"""

import json
from pathlib import Path

import pytest

from scripts import validador_fractalidade_vsa as validador
from scripts.validador_fractalidade_vsa import estimar_tokens, validar_fractalidade_slice

LIMITE_TOKENS_AGENTS = 400
LIMITE_TOKENS_README = 500

RAIZ = Path(__file__).resolve().parent.parent
MAPA = json.loads(
    (RAIZ / "modulos/04-nucleo-compartilhado/contracts/MAPA-FATIAS.json").read_text(encoding="utf-8")
)


def _pastas_fatias_e_subfatias():
    pastas = []
    for info in MAPA["fatias"].values():
        base = info["caminho"]
        pastas.append(base)
        pastas.extend(f"{base}/{ferramenta}" for ferramenta in info["ferramentas"])
    return pastas


PASTAS = _pastas_fatias_e_subfatias()


def test_mapa_tem_7_fatias_e_8_subfatias():
    assert len(MAPA["fatias"]) == 7
    assert len(PASTAS) == 15


@pytest.mark.parametrize("pasta", PASTAS)
def test_agents_md_existe_e_cabe_no_orcamento(pasta):
    alvo = RAIZ / pasta / "AGENTS.md"
    assert alvo.is_file(), f"{pasta} sem AGENTS.md"
    tokens = estimar_tokens(alvo.read_text(encoding="utf-8"))
    assert tokens < LIMITE_TOKENS_AGENTS, f"{pasta}/AGENTS.md com {tokens} tokens"


@pytest.mark.parametrize("pasta", PASTAS)
def test_readme_md_existe_e_cabe_no_orcamento(pasta):
    alvo = RAIZ / pasta / "README.md"
    assert alvo.is_file(), f"{pasta} sem README.md"
    tokens = estimar_tokens(alvo.read_text(encoding="utf-8"))
    assert tokens < LIMITE_TOKENS_README, f"{pasta}/README.md com {tokens} tokens"


def test_agents_raiz_tem_tabela_de_despacho_para_cada_fatia():
    conteudo = (RAIZ / "AGENTS.md").read_text(encoding="utf-8")
    linhas_tabela = [linha for linha in conteudo.splitlines() if linha.startswith("|")]
    for info in MAPA["fatias"].values():
        alvo = f"`{info['caminho']}/AGENTS.md`"
        assert any(alvo in linha for linha in linhas_tabela), f"tabela de despacho sem {alvo}"


def test_limites_do_validador():
    assert getattr(validador, "LIMITE_TOKENS_AGENTS", None) == LIMITE_TOKENS_AGENTS
    assert validador.LIMITE_TOKENS_README == LIMITE_TOKENS_README


def test_validador_exige_agents_e_readme(tmp_path):
    fatia = tmp_path / "fatia"
    fatia.mkdir()
    valido, erros = validar_fractalidade_slice(fatia)
    assert valido is False
    assert any("AGENTS.md" in e for e in erros)
    assert any("README.md" in e for e in erros)


def test_validador_rejeita_agents_acima_do_orcamento(tmp_path):
    fatia = tmp_path / "fatia"
    (fatia / "tests").mkdir(parents=True)
    (fatia / "README.md").write_text("# Fatia\n", encoding="utf-8")
    (fatia / "AGENTS.md").write_text("palavra " * 400, encoding="utf-8")
    valido, erros = validar_fractalidade_slice(fatia)
    assert valido is False
    assert any("AGENTS.md" in e and "tokens" in e for e in erros)


def test_validador_aceita_fatia_enxuta_sem_pastas_opcionais(tmp_path):
    """Decisão do usuário (08/10): core/skills/gates só quando a fatia tem esse conteúdo."""
    fatia = tmp_path / "fatia"
    (fatia / "aidd-x" / "tests").mkdir(parents=True)
    (fatia / "README.md").write_text("# Fatia\n", encoding="utf-8")
    (fatia / "AGENTS.md").write_text("# Regras\n", encoding="utf-8")
    valido, erros = validar_fractalidade_slice(fatia)
    assert valido is True, erros


def test_validador_exige_testes_em_algum_ponto_da_fatia(tmp_path):
    fatia = tmp_path / "fatia"
    (fatia / "core").mkdir(parents=True)
    (fatia / "README.md").write_text("# Fatia\n", encoding="utf-8")
    (fatia / "AGENTS.md").write_text("# Regras\n", encoding="utf-8")
    valido, erros = validar_fractalidade_slice(fatia)
    assert valido is False
    assert any("tests" in e for e in erros)


@pytest.mark.parametrize("nome", sorted(MAPA["fatias"]))
def test_fatias_reais_passam_no_validador(nome):
    valido, erros = validar_fractalidade_slice(RAIZ / MAPA["fatias"][nome]["caminho"])
    assert valido is True, erros
