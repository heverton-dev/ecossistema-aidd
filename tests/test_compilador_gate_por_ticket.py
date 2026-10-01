# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — TESTE DO GATE POR TICKET E MANIFESTO POR BLOCO
(scripts/compilador_plano_evolucao.py)
=============================================================================
Requisitos (Ticket 1, fronteiras-ferramentas ciclo-01):
1. Parse da linha '- **Gate do Ticket:** `<comando>`' dentro de cada ticket.
   Armazena o comando customizado em 'gate_fase'.
2. Se o ticket não declarar 'Gate do Ticket', faz fallback para GATE_TESTES
   e emite um UserWarning.
3. Parse de cabeçalhos de bloco '## Bloco N — <nome>'.
   Grava PLANO-EVOLUCAO-BLOCO-N.json por bloco, além do PLANO-EVOLUCAO.json.
=============================================================================
"""

import json
import sys
from pathlib import Path
import warnings

import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from compilador_plano_evolucao import compilar_plano_evolucao  # noqa: E402
from scaffold_auditoria import GATE_TESTES  # noqa: E402

ROTATIVO = [
    {"harness": "h1", "model": "m1", "comando_terminal": "cmd1"},
    {"harness": "h2", "model": "m2", "comando_terminal": "cmd2"},
]

PLANO_DOIS_BLOCOS = """# Plano de Evolução (Fase 2) - ferramenta-x

## Bloco 1 — Fundação
### Ticket 1: Primeiro ajuste (Refere-se a D11)
- **Falha 15-D:** `D11. Tratamento de Exceções e Fallback`
- **Artefato de Handoff:** `scripts/fallback.py`
- **Gate do Ticket:** `python -m pytest -q -p no:cacheprovider tests/test_fallback.py`
- **Requisito TDD (Red):** teste que falha.
- **Verificação (Green):** teste passa.
- **Construtor Prompt (EN):**
  - Write failing test first. Assert exit 1.
  - Implement fallback. Run pytest. Assert exit 0.

## Bloco 2 — Fechamento
### Ticket 2: Segundo ajuste (Refere-se a D13)
- **Falha 15-D:** `D13. Quality Gates (Portões)`
- **Artefato de Handoff:** `gates/G_ferramenta_x.py`
- **Requisito TDD (Red):** teste que falha.
- **Verificação (Green):** teste passa.
- **Construtor Prompt (EN):**
  - Create gate. Add bite test asserting exit 1.
"""


def test_compilador_gate_por_ticket_e_manifesto_por_bloco(tmp_path):
    pasta = tmp_path / "docs" / "auditoria" / "ferramenta-x" / "ciclo-01"
    pasta.mkdir(parents=True, exist_ok=True)
    md = pasta / "PLANO-EVOLUCAO.md"
    md.write_text(PLANO_DOIS_BLOCOS, encoding="utf-8")
    cfg = tmp_path / "CONFIG-EXECUCAO-USUARIO.json"
    cfg.write_text(json.dumps({"pipeline_evolucao_rotativo": ROTATIVO}), encoding="utf-8")

    with pytest.warns(UserWarning, match=r"[Tt]icket 2.*[Gg]ate"):
        saida_principal = compilar_plano_evolucao(md, cfg)

    # 1. Verifica manifesto completo
    manifesto_completo = json.loads(Path(saida_principal).read_text(encoding="utf-8"))
    fases = manifesto_completo["fases"]
    assert len(fases) == 2

    # Ticket 1 declara Gate do Ticket customizado
    assert fases[0]["gate_fase"] == "python -m pytest -q -p no:cacheprovider tests/test_fallback.py"

    # Ticket 2 cai no fallback padrão (GATE_TESTES)
    assert fases[1]["gate_fase"] == GATE_TESTES

    # 2. Verifica manifestos por bloco
    bloco_1_file = pasta / "PLANO-EVOLUCAO-BLOCO-1.json"
    bloco_2_file = pasta / "PLANO-EVOLUCAO-BLOCO-2.json"

    assert bloco_1_file.exists(), "PLANO-EVOLUCAO-BLOCO-1.json deve ser gerado"
    assert bloco_2_file.exists(), "PLANO-EVOLUCAO-BLOCO-2.json deve ser gerado"

    m_b1 = json.loads(bloco_1_file.read_text(encoding="utf-8"))
    m_b2 = json.loads(bloco_2_file.read_text(encoding="utf-8"))

    assert len(m_b1["fases"]) == 1
    assert m_b1["fases"][0]["ticket_id"] == "TICKET-01"
    assert m_b1["fases"][0]["gate_fase"] == "python -m pytest -q -p no:cacheprovider tests/test_fallback.py"

    assert len(m_b2["fases"]) == 1
    assert m_b2["fases"][0]["ticket_id"] == "TICKET-02"
    assert m_b2["fases"][0]["gate_fase"] == GATE_TESTES
