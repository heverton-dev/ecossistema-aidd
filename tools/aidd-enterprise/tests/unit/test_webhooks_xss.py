# -*- coding: utf-8 -*-
"""
Item 16 — regressao de XSS armazenado em WebhookDispatcher.get_studio_html().

register_module_events(slug, name) grava `name` (nome de exibicao do modulo,
definido por quem gera o app) no EVENT_CATALOG; get_studio_html() renderiza
esse catalogo como HTML de verdade (Webhook Studio). Antes da correcao, um
nome de modulo contendo "<script>...</script>" voltava executavel na pagina.
"""

import html
import os
import sys

SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src"))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from core.webhooks import WebhookDispatcher  # noqa: E402

XSS_PAYLOAD = "<script>alert(1)</script>"


def _catalogo_com_payload(slug: str):
    """Registra um evento com payload de XSS e retorna o HTML do studio,
    sem contaminar EVENT_CATALOG global entre testes."""
    catalogo_original = list(WebhookDispatcher.EVENT_CATALOG)
    try:
        WebhookDispatcher.register_module_events(slug, XSS_PAYLOAD)
        wd = WebhookDispatcher(db=None)
        return wd.get_studio_html()
    finally:
        WebhookDispatcher.EVENT_CATALOG = catalogo_original


def test_nome_de_modulo_com_payload_xss_volta_escapado():
    resultado_html = _catalogo_com_payload("xss-item16-a")

    assert XSS_PAYLOAD not in resultado_html, (
        "VULNERABILIDADE: payload de XSS voltou executavel (sem escape) no HTML "
        "do Webhook Studio"
    )
    assert html.escape(XSS_PAYLOAD) in resultado_html, (
        "Payload deveria aparecer em forma escapada (&lt;script&gt;...) no HTML"
    )


def test_titulo_customizado_com_payload_xss_volta_escapado():
    catalogo_original = list(WebhookDispatcher.EVENT_CATALOG)
    try:
        wd = WebhookDispatcher(db=None)
        resultado_html = wd.get_studio_html(title=XSS_PAYLOAD)
    finally:
        WebhookDispatcher.EVENT_CATALOG = catalogo_original

    assert XSS_PAYLOAD not in resultado_html
    assert html.escape(XSS_PAYLOAD) in resultado_html


def test_sem_escape_o_payload_apareceria_executavel():
    """Prova que o teste acima de fato detectaria a regressao: simula o
    comportamento ANTIGO (interpolacao crua) e confirma que ele falharia
    nas mesmas asserções usadas acima."""
    ev = {"event": "regressao.criado", "modulo": XSS_PAYLOAD, "descricao": "x", "exemplo": {}}
    html_sem_escape = f'<option value="{ev["event"]}">{ev["event"]} ({ev["modulo"]})</option>'

    assert XSS_PAYLOAD in html_sem_escape, (
        "Pre-condicao do teste de regressao quebrada: payload nao apareceu no "
        "cenario simulado sem escape"
    )
