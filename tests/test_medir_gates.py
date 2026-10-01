import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
import pytest
import yaml

ROOT_DIR = Path(__file__).resolve().parent.parent


def test_fake_gate_sleeps_and_exits_1(tmp_path):
    """
    TDD Step 1:
    Fake gate sleeps >= 1.0s and exits with code 1.
    Assert JSON has id, segundos >= 1, exit_code = 1, and modo.
    """
    # 1. Cria fake gate que dorme 1.05s e sai com status 1
    fake_gate_script = tmp_path / "fake_gate.py"
    fake_gate_script.write_text(
        "import sys, time\ntime.sleep(1.05)\nsys.exit(1)\n",
        encoding="utf-8"
    )

    # 2. Cria config yaml temporário estilo .pre-commit-config.yaml
    config_yaml = tmp_path / "test_pre_commit.yaml"
    config_content = {
        "repos": [
            {
                "repo": "local",
                "hooks": [
                    {
                        "id": "fake-gate-1",
                        "name": "Fake Gate Que Dorme",
                        "entry": f"python {fake_gate_script}",
                        "language": "system",
                        "always_run": True
                    }
                ]
            }
        ]
    }
    with open(config_yaml, "w", encoding="utf-8") as f:
        yaml.dump(config_content, f)

    saida_json = tmp_path / "resultado.json"

    # 3. Invoca scripts/medir_gates.py
    script_path = ROOT_DIR / "scripts" / "medir_gates.py"
    assert script_path.exists(), f"Artefato obrigatorio {script_path} ainda nao implementado"

    cmd = [
        sys.executable,
        str(script_path),
        "--config", str(config_yaml),
        "--saida", str(saida_json),
        "--modo", "rapido"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, f"medir_gates falhou com stderr: {res.stderr}"

    # 4. Valida saida JSON
    assert saida_json.exists(), "Arquivo de saida JSON nao foi gerado"
    with open(saida_json, "r", encoding="utf-8") as f:
        dados = json.load(f)

    # Deve conter lista com o registro do gate medido
    assert isinstance(dados, list), "O JSON deve ser uma lista de medições"
    assert len(dados) == 1, "Deve conter exatamente 1 medição"
    item = dados[0]
    for chave in ["id", "segundos", "exit_code", "modo"]:
        assert chave in item, f"Chave obrigatoria {chave} ausente no JSON"

    assert item["id"] == "fake-gate-1"
    assert item["segundos"] >= 1.0, f"Esperava segundos >= 1.0, obteve {item['segundos']}"
    assert item["exit_code"] == 1, f"Esperava exit_code == 1, obteve {item['exit_code']}"
    assert item["modo"] == "rapido"


def test_flags_modo_e_filtro_so(tmp_path):
    """Testa flags --modo completo, --so HOOK_ID e --saida."""
    fake_gate_a = tmp_path / "fake_a.py"
    fake_gate_a.write_text("import sys\nsys.exit(0)\n", encoding="utf-8")

    fake_gate_b = tmp_path / "fake_b.py"
    fake_gate_b.write_text("import sys\nsys.exit(0)\n", encoding="utf-8")

    config_yaml = tmp_path / "test_hooks.yaml"
    config_content = {
        "repos": [
            {
                "repo": "local",
                "hooks": [
                    {
                        "id": "gate-a",
                        "entry": f"python {fake_gate_a}"
                    },
                    {
                        "id": "gate-b",
                        "entry": f"python {fake_gate_b}"
                    }
                ]
            }
        ]
    }
    with open(config_yaml, "w", encoding="utf-8") as f:
        yaml.dump(config_content, f)

    saida_json = tmp_path / "saida_filtro.json"
    script_path = ROOT_DIR / "scripts" / "medir_gates.py"

    cmd = [
        sys.executable,
        str(script_path),
        "--config", str(config_yaml),
        "--so", "gate-b",
        "--saida", str(saida_json),
        "--modo", "completo"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0

    with open(saida_json, "r", encoding="utf-8") as f:
        dados = json.load(f)

    assert len(dados) == 1
    assert dados[0]["id"] == "gate-b"
    assert dados[0]["modo"] == "completo"
    assert dados[0]["exit_code"] == 0


def test_saida_padrao_secoes_medicoes(tmp_path, monkeypatch):
    """Testa que sem flag --saida, grava em secoes/medicoes/gates-<DATE>-<MODE>.json."""
    fake_gate = tmp_path / "fake.py"
    fake_gate.write_text("import sys\nsys.exit(0)\n", encoding="utf-8")

    config_yaml = tmp_path / "test_default.yaml"
    with open(config_yaml, "w", encoding="utf-8") as f:
        yaml.dump({
            "repos": [{"hooks": [{"id": "gate-default", "entry": f"python {fake_gate}"}]}]
        }, f)

    script_path = ROOT_DIR / "scripts" / "medir_gates.py"
    cmd = [
        sys.executable,
        str(script_path),
        "--config", str(config_yaml),
        "--modo", "rapido"
    ]
    # Executa dentro de tmp_path como cwd para verificar caminho relativo secoes/medicoes
    res = subprocess.run(cmd, cwd=str(tmp_path), capture_output=True, text=True)
    assert res.returncode == 0

    medicoes_dir = tmp_path / "secoes" / "medicoes"
    assert medicoes_dir.exists(), "Diretorio secoes/medicoes deve ser criado automaticamente"
    arquivos = list(medicoes_dir.glob("gates-*-rapido.json"))
    assert len(arquivos) >= 1, "Arquivo padrao gates-<DATE>-rapido.json deve ter sido criado"
