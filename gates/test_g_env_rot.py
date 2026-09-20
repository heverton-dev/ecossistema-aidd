#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_g_env_rot.py - Testes determinísticos do gate G_ENV_ROT (ISSUE-0015).
Comprova via execução real que o gate reprova com exit 1 quando encontra
variáveis de ambiente lidas no código que não constam em .env.example.
"""

import os
import shutil
import sys
from pathlib import Path
import pytest

from _gate_test_utils import rodar_gate

GATE_DIR = os.path.dirname(os.path.abspath(__file__))
GATE_PATH = os.path.join(GATE_DIR, "G_ENV_ROT.py")
ROOT_DIR = os.path.dirname(GATE_DIR)


def _preparar_arvore_sintetica(tmp_path: Path) -> Path:
    """Prepara a estrutura sintética com pasta gates/ e cópia do G_ENV_ROT.py."""
    fake_gates = tmp_path / "gates"
    fake_gates.mkdir(exist_ok=True)
    shutil.copy2(GATE_PATH, fake_gates / "G_ENV_ROT.py")
    return fake_gates / "G_ENV_ROT.py"


def test_g_env_rot_passa_no_repositorio():
    """Valida que o repositório atual passa com exit 0 no G_ENV_ROT."""
    proc = rodar_gate(GATE_PATH, cwd=ROOT_DIR)
    assert proc.returncode == 0, f"G_ENV_ROT reprovou inesperadamente no repo:\n{proc.stdout}\n{proc.stderr}"
    assert "SUCESSO" in proc.stdout


def test_g_env_rot_detecta_chave_ausente_reprova(tmp_path):
    """Cenário de reprovação estrita (Lei #13 / ISSUE-0015): os.getenv com chave não documentada."""
    gate_exec = _preparar_arvore_sintetica(tmp_path)

    # Cria .env.example com uma chave documentada
    env_example = tmp_path / ".env.example"
    env_example.write_text("DATABASE_URL=postgresql://localhost:5432/db\nAPI_KEY=xyz\n", encoding="utf-8")

    # Cria script python consumindo uma chave NÃO documentada via os.getenv
    app_py = tmp_path / "app.py"
    app_py.write_text(
        "import os\n"
        "db = os.getenv('DATABASE_URL')\n"
        "secret = os.getenv('CHAVE_FANTASMA_NAO_DOCUMENTADA')\n",
        encoding="utf-8"
    )

    proc = rodar_gate(str(gate_exec), cwd=str(tmp_path))
    assert proc.returncode == 1, f"Gate deveria ter saído com exit 1, mas saiu com {proc.returncode}:\n{proc.stdout}"
    assert "CHAVE_FANTASMA_NAO_DOCUMENTADA" in proc.stdout
    assert "app.py" in proc.stdout
    assert "FALHA" in proc.stdout


def test_g_env_rot_detecta_environ_subscript_ausente(tmp_path):
    """Cenário de reprovação: os.environ[...] com chave não documentada."""
    gate_exec = _preparar_arvore_sintetica(tmp_path)

    env_example = tmp_path / ".env.example"
    env_example.write_text("EXISTING_KEY=123\n", encoding="utf-8")

    service_py = tmp_path / "service.py"
    service_py.write_text(
        "import os\n"
        "val = os.environ['UNDECLARED_SUBSCRIPT_KEY']\n",
        encoding="utf-8"
    )

    proc = rodar_gate(str(gate_exec), cwd=str(tmp_path))
    assert proc.returncode == 1
    assert "UNDECLARED_SUBSCRIPT_KEY" in proc.stdout
    assert "service.py" in proc.stdout


def test_g_env_rot_detecta_process_env_js_ausente(tmp_path):
    """Cenário de reprovação: process.env.KEY em JavaScript/TypeScript sem documentação."""
    gate_exec = _preparar_arvore_sintetica(tmp_path)

    env_example = tmp_path / ".env.example"
    env_example.write_text("PORT=3000\n", encoding="utf-8")

    client_ts = tmp_path / "client.ts"
    client_ts.write_text(
        "const port = process.env.PORT;\n"
        "const backendUrl = process.env.UNDOCUMENTED_BACKEND_URL;\n",
        encoding="utf-8"
    )

    proc = rodar_gate(str(gate_exec), cwd=str(tmp_path))
    assert proc.returncode == 1
    assert "UNDOCUMENTED_BACKEND_URL" in proc.stdout
    assert "client.ts" in proc.stdout


def test_g_env_rot_detecta_chave_dinamica_undecidable(tmp_path):
    """Cenário: chaves construídas dinamicamente são explicitamente reportadas como indecidíveis."""
    gate_exec = _preparar_arvore_sintetica(tmp_path)

    env_example = tmp_path / ".env.example"
    env_example.write_text("FOO_BAR=1\n", encoding="utf-8")

    dynamic_py = tmp_path / "dynamic.py"
    dynamic_py.write_text(
        "import os\n"
        "prefix = 'FOO'\n"
        "val = os.getenv(f'{prefix}_BAR')\n"
        "val2 = os.environ[prefix + '_BAZ']\n",
        encoding="utf-8"
    )

    proc = rodar_gate(str(gate_exec), cwd=str(tmp_path))
    assert "INDECIDÍVEL" in proc.stdout
    assert "dynamic.py" in proc.stdout


def test_g_env_rot_relata_chaves_orfas(tmp_path):
    """Cenário informativo: chaves em .env.example não consumidas pelo código são listadas."""
    gate_exec = _preparar_arvore_sintetica(tmp_path)

    env_example = tmp_path / ".env.example"
    env_example.write_text(
        "USADA_NO_CODIGO=1\n"
        "CHAVE_ORFA_LEGADA=2\n",
        encoding="utf-8"
    )

    main_py = tmp_path / "main.py"
    main_py.write_text(
        "import os\n"
        "x = os.getenv('USADA_NO_CODIGO')\n",
        encoding="utf-8"
    )

    proc = rodar_gate(str(gate_exec), cwd=str(tmp_path))
    assert proc.returncode == 0
    assert "INFORMATIVO" in proc.stdout
    assert "CHAVE_ORFA_LEGADA" in proc.stdout
    assert "ÓRFÃ" in proc.stdout
