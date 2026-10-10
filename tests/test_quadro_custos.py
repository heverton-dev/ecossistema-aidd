import json
import os
import tempfile
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path("scripts").resolve()))
import quadro_custos

def test_custo_fallback_honesto_nao_medido():
    # Sem arquivo de log ou sessao desconhecida
    resultado = quadro_custos.coletar_custos_sessao(harness="claude", session_id="sessao-inexistente")
    assert resultado == "nao-medido"

def test_custo_extracao_factual_com_amostra():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Criar amostra de log jsonl do Claude Code
        log_file = Path(tmpdir) / "transcript.jsonl"
        linhas = [
            json.dumps({"type": "tool_use", "name": "mcp__codebase-memory__search_graph"}),
            json.dumps({"type": "tool_use", "name": "Skill_aidd_forge"}),
            json.dumps({"type": "usage", "input_tokens": 1250, "output_tokens": 340})
        ]
        log_file.write_text("\n".join(linhas) + "\n", encoding="utf-8")
        
        resultado = quadro_custos.coletar_custos_sessao(
            harness="claude",
            session_id="sessao-123",
            log_path=log_file
        )
        assert isinstance(resultado, dict)
        assert resultado["tokens_entrada"] == 1250
        assert resultado["tokens_saida"] == 340
        assert "aidd-forge" in resultado["skills"] or "Skill_aidd_forge" in resultado["skills"]
        assert any("codebase-memory" in m for m in resultado["mcps"])
        assert "transcript" in resultado["fonte"]
