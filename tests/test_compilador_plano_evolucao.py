# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — TESTE DO COMPILADOR DE PLANO DE EVOLUÇÃO (scripts/compilador_plano_evolucao.py)
=============================================================================
Regras (auditoria do aidd-diagnose, 2026-09-23/24):
  1. output_handoff vem da linha '**Artefato de Handoff:**' do ticket (antes
     havia um mapa fixo do aidd-melhoria aplicado a qualquer ferramenta).
  2. harness/model/comando_terminal seguem RIGOROSAMENTE
     'pipeline_evolucao_rotativo' de CONFIG-EXECUCAO-USUARIO.json (rodízio por
     ticket). Config ausente/incompleto reprova — nenhum padrão inventado.
  3. prompts_tickets/*.txt são SEMPRE em inglês telegráfico imperativo:
     o corpo vem do bloco '**Construtor Prompt (EN):**' do ticket; bloco
     ausente ou com texto não-inglês reprova.
=============================================================================
"""

import json
import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from compilador_plano_evolucao import compilar_plano_evolucao  # noqa: E402

ROTATIVO = [
    {"harness": "h1", "model": "m1", "comando_terminal": "cmd1"},
    {"harness": "h2", "model": "m2", "comando_terminal": "cmd2"},
]

PLANO = """# Plano de Evolução (Fase 2) - ferramenta-x

### Ticket 1: Primeiro ajuste (Refere-se a D11)
- **Falha 15-D:** `D11. Tratamento de Exceções e Fallback`
- **Artefato de Handoff:** `.agents/skills/ferramenta-x/scripts/fallback.py`
- **Requisito TDD (Red):** teste que falha.
- **Verificação (Green):** teste passa.
- **Construtor Prompt (EN):**
  - Write failing test first. Assert exit 1.
  - Implement fallback. Run pytest. Assert exit 0.

### Ticket 2: Segundo ajuste (Refere-se a D13)
- **Falha 15-D:** `D13. Quality Gates (Portões)`
- **Artefato de Handoff:** `gates/G_ferramenta_x.py`
- **Requisito TDD (Red):** teste que falha.
- **Verificação (Green):** teste passa.
- **Construtor Prompt (EN):**
  - Create gate. Add bite test asserting exit 1.

### Ticket 3: Terceiro ajuste (Refere-se a D14)
- **Falha 15-D:** `D14. Critério de Rejeição (Rollback)`
- **Artefato de Handoff:** `.agents/skills/ferramenta-x/scripts/rollback.py`
- **Construtor Prompt (EN):**
  - Implement rollback. Leave zero temp files.
"""


def _compilar(tmp_path: Path, texto: str, config: dict | None = None) -> dict:
    pasta = tmp_path / "docs" / "auditoria" / "ferramenta-x"
    pasta.mkdir(parents=True, exist_ok=True)
    md = pasta / "PLANO-EVOLUCAO.md"
    md.write_text(texto, encoding="utf-8")
    cfg = tmp_path / "CONFIG-EXECUCAO-USUARIO.json"
    cfg.write_text(json.dumps(config if config is not None else {"pipeline_evolucao_rotativo": ROTATIVO}), encoding="utf-8")
    saida = compilar_plano_evolucao(md, cfg)
    return json.loads(Path(saida).read_text(encoding="utf-8"))


def _prompt(tmp_path: Path, n: int) -> str:
    caminho = tmp_path / "docs" / "auditoria" / "ferramenta-x" / "prompts_tickets" / f"PROMPT-TICKET-{n:02d}.txt"
    return caminho.read_text(encoding="utf-8")


def test_handoff_vem_do_ticket_e_nao_do_aidd_melhoria(tmp_path):
    handoffs = [f["output_handoff"] for f in _compilar(tmp_path, PLANO)["fases"]]
    assert handoffs == [
        ".agents/skills/ferramenta-x/scripts/fallback.py",
        "gates/G_ferramenta_x.py",
        ".agents/skills/ferramenta-x/scripts/rollback.py",
    ]


def test_harness_model_comando_seguem_rodizio_do_config(tmp_path):
    fases = _compilar(tmp_path, PLANO)["fases"]
    esperado = [ROTATIVO[0], ROTATIVO[1], ROTATIVO[0]]
    for campo in ("harness", "model", "comando_terminal"):
        assert [f[campo] for f in fases] == [e[campo] for e in esperado]


@pytest.mark.parametrize("config", [
    {},
    {"pipeline_evolucao_rotativo": []},
    {"pipeline_evolucao_rotativo": [{"harness": "h1", "model": "m1"}]},
])
def test_config_ausente_ou_incompleto_reprova(tmp_path, config):
    with pytest.raises(ValueError, match="CONFIG-EXECUCAO-USUARIO.json"):
        _compilar(tmp_path, PLANO, config)


def test_prompt_do_ticket_e_ingles_e_cita_o_handoff(tmp_path):
    _compilar(tmp_path, PLANO)
    for n in (1, 2, 3):
        texto = _prompt(tmp_path, n)
        assert texto.isascii(), f"PROMPT-TICKET-{n:02d} nao e ingles (ASCII)"
    p2 = _prompt(tmp_path, 2)
    assert "gates/G_ferramenta_x.py" in p2
    assert "Create gate. Add bite test asserting exit 1." in p2
    assert "Portões" not in p2 and "teste que falha" not in p2
    assert "DIMENSION: D13" + chr(10) in p2


def test_ticket_sem_handoff_declarado_reprova(tmp_path):
    sem_handoff = PLANO.replace("- **Artefato de Handoff:** `gates/G_ferramenta_x.py`\n", "")
    with pytest.raises(ValueError, match="Ticket 2"):
        _compilar(tmp_path, sem_handoff)


def test_ticket_sem_prompt_ingles_reprova(tmp_path):
    sem_prompt = PLANO.replace("- **Construtor Prompt (EN):**\n  - Create gate. Add bite test asserting exit 1.\n", "")
    with pytest.raises(ValueError, match="Ticket 2"):
        _compilar(tmp_path, sem_prompt)


@pytest.mark.parametrize("trecho", [
    "  - Crie o gate. Adicione teste de mordida.",
    "  - Implementar validação do relatório.",
])
def test_prompt_em_portugues_reprova(tmp_path, trecho):
    em_pt = PLANO.replace("  - Create gate. Add bite test asserting exit 1.", trecho)
    with pytest.raises(ValueError, match="Ticket 2"):
        _compilar(tmp_path, em_pt)
