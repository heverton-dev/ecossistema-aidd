# -*- coding: utf-8 -*-
"""
Ticket 2 (skills-pocock ciclo-01, D10): contrato do texto do aidd-tickets.

Rótulo honesto: prova que a regra está escrita na skill, não que o agente a segue
(prova de comportamento = Ticket 13). O exemplo de ticket da skill é lido pelo
parser real (scripts/compilador_tickets_plano.py) para provar que o formato
continua consumível a jusante.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "componentes" / "compartilhado" / "skills" / "aidd-tickets" / "SKILL.md"

sys.path.insert(0, str(ROOT / "scripts"))
from compilador_tickets_plano import extrair_tickets_de_conteudo  # noqa: E402


def _texto() -> str:
    return SKILL.read_text(encoding="utf-8")


def _exemplo() -> str:
    m = re.search(r"```markdown\n(.*?)```", _texto(), re.DOTALL)
    assert m, "SKILL.md sem bloco ```markdown de exemplo de ticket"
    return m.group(1)


def test_sem_ordem_fixa_testes_codigo_refatoracao():
    texto = _texto()
    assert "Types/Contracts and Failing Tests" not in texto
    assert "Minimal Functional Implementation" not in texto
    assert "Strict Dependency Order" not in texto


def test_regra_fatia_vertical():
    texto = _texto()
    assert re.search(r"vertical slice", texto, re.IGNORECASE)
    assert re.search(r"one complete,? (independently )?verifiable behavio(u)?r", texto, re.IGNORECASE)
    assert re.search(r"fresh context window", texto, re.IGNORECASE)


def test_prefatoracao_primeiro():
    assert re.search(r"prefactor", _texto(), re.IGNORECASE)


def test_campo_blocked_by_por_ticket():
    texto = _texto()
    assert re.search(r"\*\*Blocked by:\*\*", texto)
    assert re.search(r"no blockers?[^\n]*start (immediately|now)", texto, re.IGNORECASE)


def test_sequencia_expand_migrate_contract():
    texto = _texto()
    m = re.search(r"expand[^\n]*migrate[^\n]*contract", texto, re.IGNORECASE)
    assert m, "sequência expand -> migrate -> contract ausente ou fora de ordem"
    assert re.search(r"in batches", texto, re.IGNORECASE)


def test_campos_nossos_mantidos():
    texto = _texto()
    assert "**Target Files:**" in texto
    assert "**Validation Command:**" in texto
    assert "[TICKET-XX]" in texto


def test_revisao_do_usuario_antes_de_publicar():
    assert re.search(r"user[^\n]*(review|approv)[^\n]*before[^\n]*publish", _texto(), re.IGNORECASE)


def test_exemplo_lido_pelo_parser_real():
    tickets = extrair_tickets_de_conteudo(_exemplo(), "SKILL.md")
    assert [t["id"] for t in tickets] == ["TICKET-01", "TICKET-02"]
    t1, t2 = tickets
    assert t1["blocked_by"] == []
    assert t2["blocked_by"] == ["TICKET-01"]
    for t in tickets:
        assert t["arquivos_alvo"], f"{t['id']} sem Target Files"
        assert t["comando_validacao"], f"{t['id']} sem Validation Command"
