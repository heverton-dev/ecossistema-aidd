# -*- coding: utf-8 -*-
"""
Ticket 13-B: Verifica que o provision_project cria apenas os módulos de domínio
quando especificados (ou presentes em C3/PLANNER), sem injetar o módulo residual 'principal'.
"""
import json
import os
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from provision_project import provision


def test_provision_com_modulos_iniciais_nao_cria_modulo_principal(tmp_path):
    """Quando modulos_iniciais são passados, não deve existir módulo 'principal'."""
    projeto_dir = tmp_path / "projeto_custom"
    provision(str(projeto_dir), modulos_iniciais=["pedidos", "clientes"])

    modulos_dir = projeto_dir / "src" / "modules"
    modulos_gerados = [m.name for m in modulos_dir.iterdir() if m.is_dir()]
    assert "pedidos" in modulos_gerados
    assert "clientes" in modulos_gerados
    assert "principal" not in modulos_gerados

    # server.py deve registrar pedidos e clientes, não principal
    server_py = (projeto_dir / "src" / "server.py").read_text(encoding="utf-8")
    assert "pedidos" in server_py
    assert "clientes" in server_py


def test_provision_lendo_c3_nao_cria_modulo_principal(tmp_path):
    """Quando HANDOFF_ENGINE_MASTER.json (C3) existe no destino com fatias, provision deve usá-las."""
    projeto_dir = tmp_path / "projeto_c3"
    projeto_dir.mkdir(parents=True)
    c3_payload = {
        "projeto_slug": "projeto-c3",
        "slices_geradas": [
            {"slice_nome": "faturamento"},
            {"slice_nome": "cobranca"}
        ]
    }
    (projeto_dir / "HANDOFF_ENGINE_MASTER.json").write_text(json.dumps(c3_payload), encoding="utf-8")

    provision(str(projeto_dir))

    modulos_dir = projeto_dir / "src" / "modules"
    modulos_gerados = [m.name for m in modulos_dir.iterdir() if m.is_dir()]
    assert "faturamento" in modulos_gerados
    assert "cobranca" in modulos_gerados
    assert "principal" not in modulos_gerados
