# -*- coding: utf-8 -*-
"""
Utilitário compartilhado pelos testes de gates de raiz que rodam o script
real de um gate via subprocess contra uma árvore/repositório sintético
(ver test_g_ecossistema_integridade.py e test_g_segredos.py). Não é um
arquivo de teste — não segue o padrão test_*.py nem G_*.py do pytest.ini,
então não é coletado como suíte.
"""

import os
import shutil
import subprocess
import sys

MAPA_DONOS_REL = os.path.join("componentes", "compartilhado", "specs", "MAPA-DONOS-FERRAMENTAS.json")
from pathlib import Path as _Path
RAIZ_REPO = str(next((p.parent for p in _Path(__file__).resolve().parents if p.name == "modulos"), _Path(__file__).resolve().parent.parent))  # raiz: pai de modulos/ (VSA) ou de gates/ (árvore sintética)


def copiar_mapa_donos(raiz_sintetica):
    """Copia o mapa de donos real (campo 'pasta' de cada ferramenta) para a árvore sintética:
    desde o ciclo-03 VSA os gates acham a pasta da ferramenta em modulos/ por ele."""
    destino = os.path.join(str(raiz_sintetica), MAPA_DONOS_REL)
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    shutil.copy2(os.path.join(RAIZ_REPO, MAPA_DONOS_REL), destino)


def rodar_gate(gate_path, cwd):
    """Executa o gate copiado via subprocess, com ambiente UTF-8, e retorna o CompletedProcess."""
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        [sys.executable, gate_path],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env
    )
