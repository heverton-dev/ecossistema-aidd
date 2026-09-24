# -*- coding: utf-8 -*-
"""
Teste de Quality Gate Determinístico e Rótulo Honesto (Ticket 6 / D13 / DoD 3 / DoD 6).
Exige que `gates/G_amelhoria.py` aprove saídas com rótulo honesto ("Sugestão de refatoração...")
e reprove terminantemente com exit 1 afirmações imperativas enganosas como "Refatoração concluída".
"""

import json
import subprocess
import sys
from pathlib import Path
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
GATE_SCRIPT = ROOT_DIR / "gates" / "G_amelhoria.py"


def executar_gate_amelhoria(caminho_relatorio: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(GATE_SCRIPT), "--relatorio", str(caminho_relatorio)],
        capture_output=True,
        text=True,
        cwd=str(ROOT_DIR),
        encoding="utf-8",
        errors="replace",
    )


def test_gate_rejeita_afirmacao_refatoracao_concluida(tmp_path):
    """Garante que relatório afirmando falsamente 'Refatoração concluída' seja vetado com exit 1."""
    relatorio_desonesto = tmp_path / "relatorio_desonesto.json"
    dados = {
        "pedido": "Modernizar banco de dados",
        "nota_atual": "9.0",
        "evidencia": "Migracao realizada",
        "resumo": "Refatoração concluída com sucesso no banco de dados.",
        "recomendacao": "Refatoração concluída integralmente."
    }
    relatorio_desonesto.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")

    res = executar_gate_amelhoria(relatorio_desonesto)
    assert res.returncode == 1
    assert "Rótulo Desonesto" in res.stdout or "proibido" in res.stdout.lower() or "violação" in res.stdout.lower()


def test_gate_aprova_rotulo_honesto(tmp_path):
    """Garante que relatório contendo 'Sugestão de refatoração...' receba aprovação (exit 0)."""
    relatorio_honesto = tmp_path / "relatorio_honesto.json"
    dados = {
        "pedido": "Modernizar banco de dados",
        "nota_atual": "6.0",
        "evidencia": "Queries N+1 detectadas em 4 endpoints",
        "resumo": "Sugestão de refatoração para otimização de consultas e indices.",
        "recomendacao": "Sugestão de refatoração aprovada para etapa de planejamento."
    }
    relatorio_honesto.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")

    res = executar_gate_amelhoria(relatorio_honesto)
    assert res.returncode == 0
    assert "APROVADO" in res.stdout or "EXIT 0" in res.stdout
