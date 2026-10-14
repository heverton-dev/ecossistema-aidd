# -*- coding: utf-8 -*-
"""ETAPA_09 (Ticket 4 da ETAPA_05): defeitos do extrator de tokens do Mobbin, provados com imagens sintéticas.

Medidos em 13/10/2026 sobre telas reais: (1) a cor primária saía quase branca (#fefefe) porque o laço
parava ao juntar 6 tons de fundo; (2) a barra escura "curated by Mobbin" (~48 px no rodapé) contaminava a
cor; (3) o cliente usava `image_url` (deprecado) em vez de `image.url`; (4) só 1 tela era considerada.
Tipografia por nome do app e espaçamentos/raios constantes continuam sendo convenção (a imagem não informa
fonte nem raio): isso não é tratado como defeito corrigido, só declarado no resultado.
"""
from io import BytesIO

import pytest
from PIL import Image, ImageDraw

from componentes.compartilhado.mcps.mobbin_mcp import token_extractor as te

TEAL = (15, 118, 110)
AZUL = (29, 78, 216)


def _tela_sintetica(botao=TEAL, rodape=True, largura=768, altura=600):
    """Fundo com 12 tons de quase-branco (como imagem real com anti-aliasing), um botão colorido e a
    barra escura de rodapé de ~48 px."""
    img = Image.new("RGB", (largura, altura), (255, 255, 255))
    d = ImageDraw.Draw(img)
    faixa = (altura - 48) // 12
    for i in range(12):
        tom = 255 - i
        d.rectangle([0, i * faixa, largura, (i + 1) * faixa], fill=(tom, tom, tom))
    d.rectangle([300, 250, 470, 300], fill=botao)  # botão primário
    if rodape:
        d.rectangle([0, altura - 48, largura, altura], fill=(24, 24, 24))
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _hex(rgb):
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def _distancia(hex_a, hex_b):
    a = [int(hex_a[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(hex_b[i:i + 2], 16) for i in (1, 3, 5)]
    return sum(abs(x - y) for x, y in zip(a, b))


def test_primaria_e_a_cor_do_botao_e_nao_um_tom_de_branco():
    tokens = te.extrair_paleta_imagem(_tela_sintetica())
    assert _distancia(tokens["light"]["primary"], _hex(TEAL)) < 48, tokens["light"]["primary"]
    assert tokens["modo"] == "light"


def test_rodape_escuro_nao_entra_na_paleta_nem_vira_modo_dark():
    tokens = te.extrair_paleta_imagem(_tela_sintetica())
    assert all(_distancia(c, "#181818") > 30 for c in tokens["paleta_extraida"]), tokens["paleta_extraida"]


def test_recortar_rodape_tira_a_barra_proporcional_a_largura():
    img = Image.open(BytesIO(_tela_sintetica()))
    recortada = te.recortar_rodape(img)
    assert recortada.height == img.height - 48
    pequena = Image.new("RGB", (384, 300), (255, 255, 255))
    assert te.recortar_rodape(pequena).height == 300 - 24


def test_varias_telas_votam_na_cor_primaria():
    telas = {
        "u1": _tela_sintetica(TEAL), "u2": _tela_sintetica((16, 120, 112)), "u3": _tela_sintetica(AZUL),
    }
    candidatas = [{"id": i, "app_name": "App", "image": {"url": u}} for i, u in zip("abc", telas)]
    tokens = te.extrair_tokens_de_telas(candidatas, baixar=lambda url: telas[url])
    assert _distancia(tokens["cores"]["light"]["primary"], _hex(TEAL)) < 48
    assert [o["screen_id"] for o in tokens["origem_referencias"]] == ["a", "b", "c"]
    assert tokens["telas_analisadas"] == 3


def test_tela_sem_imagem_baixavel_nao_derruba_as_outras():
    def baixar(url):
        if url == "ruim":
            raise OSError("404")
        return _tela_sintetica(TEAL)

    telas = [{"id": "x", "image": {"url": "ruim"}}, {"id": "y", "image": {"url": "ok"}}]
    tokens = te.extrair_tokens_de_telas(telas, baixar=baixar)
    assert tokens["telas_analisadas"] == 1


def test_usa_image_url_novo_e_cai_no_deprecado_so_se_faltar():
    chamadas = []

    def baixar(url):
        chamadas.append(url)
        return _tela_sintetica()

    te.extrair_tokens_mobbin({"id": "1", "image": {"url": "novo"}, "image_url": "velho"}, baixar=baixar)
    te.extrair_tokens_mobbin({"id": "2", "image_url": "velho"}, baixar=baixar)
    assert chamadas == ["novo", "velho"]


def test_resultado_declara_o_que_e_convencao_e_nao_extraido():
    tokens = te.extrair_tokens_mobbin({"id": "1", "image": {"url": "u"}}, baixar=lambda url: _tela_sintetica())
    assert "tipografia" in tokens["nao_extraido_da_imagem"]
    assert "espacamentos" in tokens["nao_extraido_da_imagem"]
    assert "raios_borda" in tokens["nao_extraido_da_imagem"]


# --- telas reais quase cinzas (Linear): sem cor de marca confiável, o extrator não pode inventar uma --------

def _tela_cinza(largura=768, altura=600, destaque=True):
    img = Image.new("RGB", (largura, altura), (248, 248, 248))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 160, altura], fill=(236, 236, 236))      # sidebar cinza
    d.rectangle([200, 100, 700, 400], fill=(255, 255, 255))     # cartão branco
    if destaque:
        d.rectangle([220, 120, 240, 128], fill=(120, 131, 212))  # um traço de destaque minúsculo
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_tela_sem_cor_de_marca_nao_inventa_primaria_quase_branca():
    tokens = te.extrair_paleta_imagem(_tela_cinza())
    primaria = tokens["light"]["primary"]
    r, g, b = (int(primaria[i:i + 2], 16) for i in (1, 3, 5))
    assert max(r, g, b) - min(r, g, b) > 30 or tokens["primaria_detectada"] is False
    if tokens["primaria_detectada"] is False:
        assert primaria == "#3b82f6"  # neutro declarado, não um tom de fundo
    assert "primaria_detectada" in tokens


def test_tela_totalmente_cinza_declara_primaria_nao_detectada():
    tokens = te.extrair_paleta_imagem(_tela_cinza(destaque=False))
    assert tokens["primaria_detectada"] is False
    assert tokens["light"]["primary"] == "#3b82f6"


def test_agregado_sem_nenhuma_primaria_detectada_declara_isso():
    telas = [{"id": "a", "image": {"url": "u"}}, {"id": "b", "image": {"url": "u"}}]
    tokens = te.extrair_tokens_de_telas(telas, baixar=lambda url: _tela_cinza(destaque=False))
    assert tokens["cores"]["primaria_detectada"] is False
    assert tokens["cores"]["light"]["primary"] == "#3b82f6"


def test_agregado_ignora_tela_sem_primaria_quando_outra_tem():
    imagens = {"cinza": _tela_cinza(destaque=False), "teal": _tela_sintetica(TEAL)}
    telas = [{"id": "g", "image": {"url": "cinza"}}, {"id": "t", "image": {"url": "teal"}}]
    tokens = te.extrair_tokens_de_telas(telas, baixar=lambda url: imagens[url])
    assert tokens["cores"]["primaria_detectada"] is True
    assert _distancia(tokens["cores"]["light"]["primary"], _hex(TEAL)) < 48
