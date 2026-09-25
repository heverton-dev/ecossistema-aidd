# -*- coding: utf-8 -*-
"""
Ticket 1 (skills-pocock ciclo-01, D8): contrato do texto do aidd-diagnose.

Rótulo honesto: prova que a regra está escrita na skill, não que o agente a segue
(prova de comportamento = Ticket 13).
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL_REL = "componentes/compartilhado/skills/aidd-diagnose/SKILL.md"
SKILL = ROOT / SKILL_REL
GATE = ROOT / "gates" / "G_aidd_diagnose.py"
# Teste real, existente e verde; não pode ser este arquivo (o gate rodaria pytest nele em loop).
TESTE_REGRESSAO_EXEMPLO = "tests/test_diagnose_rollback.py"
# Base fixa (merge do aidd-diagnose ciclo-01): comparar com HEAD vira tautologia depois do commit.
BASE_REF = "f6cdb15"


def _texto() -> str:
    return SKILL.read_text(encoding="utf-8")


def _texto_base() -> str:
    res = subprocess.run(
        ["git", "show", f"{BASE_REF}:{SKILL_REL}"],
        cwd=str(ROOT), capture_output=True, check=True,
    )
    return res.stdout.decode("utf-8")


def _bloco(texto: str, inicio: str, fim: str) -> str:
    ini = texto.index(inicio)
    return texto[ini:texto.index(fim, ini)]


def _fase2(texto: str) -> str:
    return _bloco(texto, "2. **Graph Blast Radius Analysis:**", "\n3. **")


def test_sem_hipotese_unica():
    # A fonte dizia "exactly ONE testable hypothesis": casar com palavras no meio.
    assert not re.search(r"exactly\s+ONE\b[^\n]*\bhypothesis", _texto())
    assert "Single Hypothesis Formulation" not in _texto()


def test_fase1_loop_vermelho_ja_executado():
    fase1 = _bloco(_texto(), "1. **", "\n2. **")
    assert re.search(r"already run", fase1, re.IGNORECASE)
    assert re.search(r"red on this bug", fase1, re.IGNORECASE)
    assert re.search(r"deterministic", fase1, re.IGNORECASE)
    assert re.search(r"fast", fase1, re.IGNORECASE)


def test_sem_loop_para_e_pede_ao_usuario():
    fase1 = _bloco(_texto(), "1. **", "\n2. **")
    assert re.search(r"no loop", fase1, re.IGNORECASE)
    assert re.search(r"stop", fase1, re.IGNORECASE)
    assert re.search(r"redacted artifact", fase1, re.IGNORECASE)


def test_etapa_de_minimizacao():
    assert re.search(r"\bminimi[sz]e\b", _texto(), re.IGNORECASE)
    assert re.search(r"one element at a time", _texto(), re.IGNORECASE)


def test_tres_a_cinco_hipoteses_em_ordem():
    fase3 = _bloco(_texto(), "3. **", "\n4. **")
    assert re.search(r"3[–-]5 falsifiable", fase3, re.IGNORECASE)
    assert re.search(r"ranked", fase3, re.IGNORECASE)
    assert re.search(r"show(n)? .*user", fase3, re.IGNORECASE)
    assert re.search(r"one at a time", fase3, re.IGNORECASE)


def test_lista_candidata_antes_de_hipoteses_ativas():
    texto = _texto()
    idx_cand = texto.find("## Hipóteses candidatas")
    idx_ativas = texto.find("HIPOTESES ATIVAS:")
    assert idx_cand != -1 and idx_ativas != -1
    assert idx_cand < idx_ativas
    assert re.search(r"exactly one active", texto, re.IGNORECASE)


def test_prefixo_debug_nos_logs_temporarios():
    texto = _texto()
    assert "[DEBUG-" in texto
    # A limpeza real (rollback.py) ainda depende do marcador de fim de linha.
    assert "AIDD-DIAGNOSE-TEMP" in texto


def test_sem_ponto_de_teste_vira_achado():
    assert re.search(r"no (correct )?(test )?seam", _texto(), re.IGNORECASE)
    assert re.search(r"finding", _texto(), re.IGNORECASE)


def test_fase2_identica_a_base():
    assert _fase2(_texto()) == _fase2(_texto_base())


def test_secao_cli_e_comandos_preservados():
    atual, head = _texto(), _texto_base()
    assert _bloco(atual, "## CLI (single entry point)", "## 5-Phase Protocol") == \
        _bloco(head, "## CLI (single entry point)", "## 5-Phase Protocol")
    for comando in (
        'diagnose registrar --fase 1 --comando "<repro>"',
        'diagnose registrar --fase 3 --hipotese "<hypothesis>"',
        "diagnose worktree --slug <slug>",
        'diagnose registrar --fase 4 --descartada "<h>" --prova "<evidence>"',
        "diagnose limpar --slug <slug>",
        "diagnose relatorio ...",
        "handoff.py emitir",
    ):
        assert comando in atual, comando


def test_menos_de_150_linhas():
    assert len(_texto().splitlines()) < 150


def test_gate_aprova_relatorio_de_exemplo(tmp_path):
    assert (ROOT / TESTE_REGRESSAO_EXEMPLO).is_file()
    relatorio = tmp_path / "RELATORIO-CAUSA-RAIZ.md"
    relatorio.write_text(
        "# Relatório de Causa Raiz\n\n"
        "- **Comando**: `python -m pytest tests/test_diagnose_rollback.py -q`\n"
        "- 5 execuções com o mesmo resultado\n"
        "- Resultado Determinístico: Sim\n\n"
        "## Hipóteses candidatas\n\n"
        "1. limpar() ignora arquivo untracked\n"
        "2. marcador com espaço extra não casa\n"
        "3. worktree removida antes da varredura\n\n"
        "HIPOTESES ATIVAS:\n"
        "  - limpar() ignora arquivo untracked\n\n"
        "HIPOTESES DESCARTADAS:\n"
        "  (Nenhuma)\n\n"
        "## Teste de Regressão\n\n"
        f"- **Teste de Regressão**: `{TESTE_REGRESSAO_EXEMPLO}`\n"
        "- **Resultado Antes do Fix**: FALHA\n"
        "- **Resultado Após o Fix**: PASSOU\n",
        encoding="utf-8",
    )
    res = subprocess.run(
        [sys.executable, str(GATE), "--relatorio", str(relatorio)],
        cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8", timeout=600,
    )
    assert res.returncode == 0, res.stdout + res.stderr
