# -*- coding: utf-8 -*-
"""Interface publica da fatia 01-governanca-e-qualidade: unico ponto que outras fatias podem usar (ciclo-03 T10).

Expoe so o que outras fatias consomem hoje. Carregar por caminho, com nome de modulo unico
(ex.: importlib.util.spec_from_file_location("interface_01_governanca_e_qualidade", <este arquivo>)).
"""
import sys
from pathlib import Path

_FATIA = Path(__file__).resolve().parent
RAIZ_FORGE = _FATIA / "core" / "aidd-forge"
RAIZ_PLANNER = _FATIA / "core" / "aidd-planner"

# A copia do forge desta fatia vence um aidd_forge instalado em outro checkout.
if str(RAIZ_FORGE) not in sys.path:
    sys.path.insert(0, str(RAIZ_FORGE))

from aidd_forge.core.almoxarifado import caminho_peca, obter_peca  # noqa: E402

__all__ = ["RAIZ_FORGE", "RAIZ_PLANNER", "caminho_peca", "obter_peca"]
