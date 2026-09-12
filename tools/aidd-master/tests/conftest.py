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
import materializador
import assinatura_manifesto

@pytest.fixture(autouse=True)
def isola_raiz_canonica_do_ecossistema(request, tmp_path, monkeypatch):
    if request.node.get_closest_marker('raiz_real'):
        return
    raiz_fake = tmp_path / '_ecossistema_fake_root'
    monkeypatch.setattr(materializador, '_default_ecossistema_root', lambda: raiz_fake)
    # Isola também a descoberta de chaves Ed25519 do manifesto: sem isto, os
    # testes usariam a chave privada/pública REAIS do repositório (fora do
    # tmp_path), vazando estado entre testes e arriscando ler/escrever em
    # 'chaves/manifesto/' de verdade.
    monkeypatch.setattr(assinatura_manifesto, '_default_ecossistema_root', lambda: raiz_fake)
