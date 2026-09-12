# -*- coding: utf-8 -*-
import os
import sys

_TOOL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CORE = os.path.join(_TOOL_ROOT, "src", "core")
if _TOOL_ROOT not in sys.path:
    sys.path.insert(0, _TOOL_ROOT)
if _CORE not in sys.path:
    sys.path.insert(0, _CORE)

import pytest
try:
    import materializador
except ImportError:
    materializador = None

@pytest.fixture(autouse=True)
def isola_raiz_canonica_do_ecossistema(request, tmp_path, monkeypatch):
    if request.node.get_closest_marker('raiz_real'):
        return
    if materializador and hasattr(materializador, '_default_ecossistema_root'):
        raiz_fake = tmp_path / '_ecossistema_fake_root'
        monkeypatch.setattr(materializador, '_default_ecossistema_root', lambda: raiz_fake)
