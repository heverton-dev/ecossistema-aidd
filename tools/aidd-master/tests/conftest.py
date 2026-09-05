# -*- coding: utf-8 -*-
import os
import sys

_CORE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "core")
if _CORE not in sys.path:
    sys.path.insert(0, _CORE)

import pytest
import materializador

@pytest.fixture(autouse=True)
def isola_raiz_canonica_do_ecossistema(request, tmp_path, monkeypatch):
    if request.node.get_closest_marker('raiz_real'):
        return
    raiz_fake = tmp_path / '_ecossistema_fake_root'
    monkeypatch.setattr(materializador, '_default_ecossistema_root', lambda: raiz_fake)
