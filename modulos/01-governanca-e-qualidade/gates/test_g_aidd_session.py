# -*- coding: utf-8 -*-
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GATE_SCRIPT = ROOT / "gates" / "G_aidd_session.py"


def test_gate_valida_historico_correto(tmp_path):
    json_path = tmp_path / "historico.json"
    md_path = tmp_path / "INDICE.md"

    json_path.write_text(json.dumps({
        "versao": "1.0",
        "sessoes": [{"id": "s1", "harness": "claude"}]
    }), encoding="utf-8")

    md_path.write_text("# 📑 Índice Canônico de Sessões Agênticas\n", encoding="utf-8")

    # Testa modulo direto
    from gates.G_aidd_session import validar_historico
    assert validar_historico(json_path, md_path) == 0


def test_gate_rejeita_arquivo_inexistente(tmp_path):
    json_path = tmp_path / "inexistente.json"
    res = subprocess.run([sys.executable, str(GATE_SCRIPT)], cwd=str(tmp_path), capture_output=True)
    assert res.returncode == 1


def test_gate_rejeita_json_sem_sessoes(tmp_path):
    json_path = tmp_path / "historico.json"
    json_path.write_text(json.dumps({"versao": "1.0"}), encoding="utf-8")
    from gates.G_aidd_session import validar_historico
    exit_code = validar_historico(json_path)
    assert exit_code == 1
