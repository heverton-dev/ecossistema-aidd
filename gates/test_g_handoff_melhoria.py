# -*- coding: utf-8 -*-
"""Prova que morde (Lei #13) do gate G_HANDOFF_MELHORIA: reprova (exit 1) sem handoff íntegro."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "gates"))
sys.path.insert(0, str(ROOT_DIR / ".agents" / "skills" / "aidd-melhoria" / "scripts"))

import G_HANDOFF_MELHORIA as gate  # noqa: E402
import handoff  # noqa: E402


def _handoff_sucesso(tmp_path: Path) -> Path:
    relatorio = tmp_path / "docs" / "melhorias" / "relatorio.json"
    relatorio.parent.mkdir(parents=True)
    relatorio.write_text('{"nota_atual": "7"}', encoding="utf-8")
    destino = tmp_path / "handoff-melhoria.json"
    handoff.emitir_handoff(destino, status="SUCESSO", codigo_saida=0, repo_root=tmp_path, artefatos=[relatorio])
    return destino


def test_gate_aprova_handoff_integro(tmp_path):
    destino = _handoff_sucesso(tmp_path)
    codigo = gate.main(["--handoff", str(destino), "--repo-root", str(tmp_path)])
    assert codigo == 0


def test_gate_reprova_handoff_ausente(tmp_path):
    codigo = gate.main(["--handoff", str(tmp_path / "handoff-melhoria.json"), "--repo-root", str(tmp_path)])
    assert codigo == 1


def test_gate_reprova_handoff_adulterado(tmp_path):
    destino = _handoff_sucesso(tmp_path)
    dados = json.loads(destino.read_text(encoding="utf-8"))
    dados["codigo_saida"] = 0
    dados["status"] = "SUCESSO"
    dados["emitido_em"] = "2000-01-01T00:00:00+00:00"
    destino.write_text(json.dumps(dados), encoding="utf-8")
    codigo = gate.main(["--handoff", str(destino), "--repo-root", str(tmp_path)])
    assert codigo == 1


def test_gate_reprova_handoff_de_falha(tmp_path):
    destino = tmp_path / "handoff-melhoria.json"
    handoff.emitir_handoff(destino, status="FALHA", codigo_saida=1, repo_root=tmp_path, erro="manifesto inválido")
    codigo = gate.main(["--handoff", str(destino), "--repo-root", str(tmp_path)])
    assert codigo == 1
