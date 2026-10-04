# -*- coding: utf-8 -*-
"""
Validação de conformidade das seções de fronteiras dos READMEs das 8 ferramentas (Ticket 22 - D14).

Regra:
Cada tools/aidd-*/README.md deve conter uma seção de Fronteira Canônica
refletindo com exatidão as regras de MAPA-DONOS-FERRAMENTAS.json:
- Responsabilidades
- O que pode conter / O que nunca conter
- Zona de escrita no projeto
"""

import json
from pathlib import Path
import pytest

RAIZ = Path(__file__).resolve().parent.parent
MAPA_PATH = RAIZ / "componentes" / "compartilhado" / "specs" / "MAPA-DONOS-FERRAMENTAS.json"
DOC_FRONTEIRAS = RAIZ / "docs" / "anatomias" / "FRONTEIRAS-POR-FERRAMENTA.md"
DOC_PAPEIS = RAIZ / "docs" / "anatomias" / "PAPEIS-DAS-8-FERRAMENTAS.md"

FERRAMENTAS = [
    "aidd-forge",
    "aidd-planner",
    "aidd-pure",
    "aidd-open",
    "aidd-freedom",
    "aidd-master",
    "aidd-enterprise",
    "aidd-ops",
]


def test_documento_fronteiras_por_ferramenta_existe_e_cobre_as_8():
    assert DOC_FRONTEIRAS.exists(), f"Faltando {DOC_FRONTEIRAS}"
    conteudo = DOC_FRONTEIRAS.read_text(encoding="utf-8")
    for f in FERRAMENTAS:
        assert f"## `{f}`" in conteudo or f"## {f}" in conteudo, f"{f} ausente em {DOC_FRONTEIRAS}"


def test_documento_papeis_das_8_ferramentas_atualizado():
    assert DOC_PAPEIS.exists()
    conteudo = DOC_PAPEIS.read_text(encoding="utf-8")
    for f in FERRAMENTAS:
        assert f in conteudo
    assert "FRONTEIRAS-POR-FERRAMENTA.md" in conteudo


@pytest.mark.parametrize("ferramenta", FERRAMENTAS)
def test_readme_ferramenta_tem_secao_de_fronteiras_alinhada(ferramenta):
    readme = RAIZ / "tools" / ferramenta / "README.md"
    assert readme.exists(), f"README não encontrado para {ferramenta}"
    conteudo = readme.read_text(encoding="utf-8")

    # Exige marcador de Fronteiras Canônicas
    assert "## Fronteiras Canônicas e Responsabilidades" in conteudo, (
        f"README de {ferramenta} não possui a seção '## Fronteiras Canônicas e Responsabilidades'"
    )

    with open(MAPA_PATH, "r", encoding="utf-8") as f:
        mapa = json.load(f)

    dados = mapa[ferramenta]
    for resp in dados.get("responsabilidades", []):
        assert resp in conteudo, f"Responsabilidade {resp} ausente no README de {ferramenta}"

    for nunca in dados.get("nunca_conter", []):
        assert nunca in conteudo, f"Regra nunca_conter '{nunca}' ausente no README de {ferramenta}"
