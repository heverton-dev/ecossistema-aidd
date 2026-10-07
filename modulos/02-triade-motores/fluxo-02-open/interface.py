# -*- coding: utf-8 -*-
"""Interface publica da fatia fluxo-02-open: unico ponto que outras fatias podem usar (ciclo-03 T10).

Expoe so o que outras fatias consomem hoje. Carregar por caminho, com nome de modulo unico
(ex.: importlib.util.spec_from_file_location("interface_fluxo_02_open", <este arquivo>)).
"""
from pathlib import Path

_FATIA = Path(__file__).resolve().parent
RAIZ_OPEN = _FATIA / "core" / "aidd-open"

__all__ = ["RAIZ_OPEN"]
