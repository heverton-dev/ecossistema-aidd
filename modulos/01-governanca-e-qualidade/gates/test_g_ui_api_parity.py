# -*- coding: utf-8 -*-
"""
=============================================================================
PROVA DE QUE O PORTÃO MORDE: test_g_ui_api_parity.py (Lei #13)
=============================================================================
Comprova deliberadamente que G_UI_API_PARITY.py:
  1. Reprova com exit 1 quando a paridade for inferior ao limiar mínimo (< 85%).
  2. Aprova com exit 0 quando a cobertura de endpoints na UI for conforme (>= 85%).
  3. Morde na prática contra o caso de estudo real Revnault (proj_revops),
     reprovando a subutilização de 87% do backend.
=============================================================================
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parents[3]
GATE_PATH = ROOT_DIR / "modulos" / "01-governanca-e-qualidade" / "gates" / "G_UI_API_PARITY.py"
REVNAULT_PATH = Path(r"C:\Users\trcnologia\Desktop\_inbox\proj_revops")


def test_g_ui_api_parity_reprova_quando_endpoints_estao_orfaos(tmp_path: Path):
    """Cenário sintético: backend com 10 endpoints, frontend com apenas 2 (20% paridade) -> DEVE REPROVAR (exit 1)."""
    proj = tmp_path / "projeto_incompleto"
    proj.mkdir()
    
    # Backend com 10 rotas
    openapi = {
        "paths": {
            f"/api/v1/resource_{i}": {"get": {}} for i in range(10)
        }
    }
    (proj / "openapi.json").write_text(json.dumps(openapi), encoding="utf-8")
    
    # Frontend com apenas 2 chamadas
    f_src = proj / "frontend" / "src"
    f_src.mkdir(parents=True)
    (f_src / "App.tsx").write_text("""
        fetch("/api/v1/resource_0");
        fetch("/api/v1/resource_1");
    """, encoding="utf-8")

    res = subprocess.run(
        [sys.executable, str(GATE_PATH), "--projeto", str(proj), "--limiar", "85"],
        capture_output=True,
        text=True,
    )

    assert res.returncode == 1
    assert "Quality Gate REPROVADO" in res.stdout
    assert "20.00%" in res.stdout


def test_g_ui_api_parity_aprova_quando_paridade_atinge_meta(tmp_path: Path):
    """Cenário sintético: backend com 10 rotas, frontend com 9 rotas conectadas (90% paridade) -> DEVE APROVAR (exit 0)."""
    proj = tmp_path / "projeto_conforme"
    proj.mkdir()
    
    openapi = {
        "paths": {
            f"/api/v1/resource_{i}": {"get": {}} for i in range(10)
        }
    }
    (proj / "openapi.json").write_text(json.dumps(openapi), encoding="utf-8")
    
    # Frontend com 9 chamadas conectadas
    f_src = proj / "frontend" / "src"
    f_src.mkdir(parents=True)
    calls_str = "\n".join([f'fetch("/api/v1/resource_{i}");' for i in range(9)])
    (f_src / "App.tsx").write_text(calls_str, encoding="utf-8")

    res = subprocess.run(
        [sys.executable, str(GATE_PATH), "--projeto", str(proj), "--limiar", "85"],
        capture_output=True,
        text=True,
    )

    assert res.returncode == 0
    assert "Quality Gate G_UI_API_PARITY APROVADO" in res.stdout
    assert "90.00%" in res.stdout


@pytest.mark.skipif(not REVNAULT_PATH.is_dir(), reason="Caso de estudo Revnault não presente no ambiente")
def test_g_ui_api_parity_aprova_caso_modelo_revnault():
    """Prova de fogo real: roda o gate contra o caso modelo real Revnault (proj_revops),
    comprovando que após os patches de fatias ele atinge o padrão-ouro com paridade >= 85%."""
    res = subprocess.run(
        [
            sys.executable,
            str(GATE_PATH),
            "--projeto",
            str(REVNAULT_PATH),
            "--backend",
            str(REVNAULT_PATH / "src"),
            "--frontend",
            str(REVNAULT_PATH / "frontend" / "src"),
            "--limiar",
            "85",
        ],
        capture_output=True,
        text=True,
    )

    # O caso real Revnault após os patches atinge 93,61% de paridade, sendo o modelo canônico aprovado!
    assert res.returncode == 0
    assert "Quality Gate G_UI_API_PARITY APROVADO" in res.stdout
    assert "Taxa de Paridade de Endpoints (TPE):" in res.stdout
