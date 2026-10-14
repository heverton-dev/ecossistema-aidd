# -*- coding: utf-8 -*-
"""ETAPA_09 (Tickets 3, 4 e 6 da ETAPA_05): Mobbin no planner.

  - cliente: levanta exceção (nunca `sys.exit` dentro de biblioteca), só aceita `standard|deep`,
    e `status` nunca imprime caractere da chave;
  - referências: uma consulta por tela a partir da spec, modo `standard`, cache por hash, só
    tokens e links no `referencias-ui.json` (nunca as imagens), fallback pela spec (nunca em silêncio).
"""
import json
import os
import sys
from io import BytesIO

import pytest
from PIL import Image, ImageDraw

_PLANNER_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PLANNER_DIR not in sys.path:
    sys.path.insert(0, _PLANNER_DIR)

from src.core_planner import mobbin_client, referencias

CHAVE = "ABCD1234efgh5678WXYZ"  # pragma: allowlist secret
DIRECAO = {"tom": "sóbrio", "cor_primaria": "#0F766E", "referencias": ["Linear", "Stripe"], "publico": "atendentes"}


class _Resp:
    def __init__(self, status=200, corpo=None):
        self.status_code = status
        self._corpo = corpo if corpo is not None else {"screens": []}

    def json(self):
        return self._corpo

    def raise_for_status(self):
        if self.status_code >= 400:
            raise mobbin_client.requests.HTTPError(str(self.status_code))


@pytest.fixture
def com_chave(monkeypatch):
    monkeypatch.setenv("MOBBIN_API_KEY", CHAVE)
    monkeypatch.setenv("MOBBIN_API_URL", "https://api.mobbin.com")


# --- cliente ----------------------------------------------------------------------------------------

def test_401_levanta_excecao_e_nao_encerra_o_processo(com_chave, monkeypatch):
    monkeypatch.setattr(mobbin_client.requests, "post", lambda *a, **k: _Resp(401))
    with pytest.raises(mobbin_client.MobbinError) as erro:
        mobbin_client.executar_busca("dashboard")
    assert "401" in str(erro.value) and CHAVE not in str(erro.value)


def test_chave_ausente_levanta_excecao(monkeypatch):
    monkeypatch.delenv("MOBBIN_API_KEY", raising=False)
    with pytest.raises(mobbin_client.MobbinError):
        mobbin_client.executar_busca("dashboard")


def test_falha_de_rede_levanta_mobbin_error(com_chave, monkeypatch):
    def cai(*a, **k):
        raise mobbin_client.requests.ConnectionError("fora do ar")
    monkeypatch.setattr(mobbin_client.requests, "post", cai)
    with pytest.raises(mobbin_client.MobbinError):
        mobbin_client.executar_busca("dashboard")


@pytest.mark.parametrize("modo", ["fast", "rapido", ""])
def test_modo_so_aceita_standard_ou_deep(com_chave, modo):
    with pytest.raises(ValueError):
        mobbin_client.executar_busca("dashboard", mode=modo)


def test_busca_envia_modo_standard_por_padrao(com_chave, monkeypatch):
    enviado = {}

    def post(url, headers=None, json=None, timeout=None):
        enviado.update(json)
        return _Resp(200)
    monkeypatch.setattr(mobbin_client.requests, "post", post)
    mobbin_client.executar_busca("dashboard")
    assert enviado["mode"] == "standard" and enviado["platform"] == "web"


def test_status_nao_imprime_nenhum_caractere_da_chave(com_chave, capsys):
    assert mobbin_client.cmd_status() == 0
    saida = capsys.readouterr().out
    for trecho in (CHAVE, CHAVE[:4], CHAVE[-4:]):
        assert trecho not in saida
    assert "SIM" in saida.upper()


def test_status_sem_chave_sai_com_1(monkeypatch, capsys):
    monkeypatch.delenv("MOBBIN_API_KEY", raising=False)
    assert mobbin_client.cmd_status() == 1


# --- consultas e cache ----------------------------------------------------------------------------

def test_consultas_saem_da_spec_ancoradas_nos_apps_de_referencia():
    consultas = referencias.consultas_da_spec(DIRECAO, "comercio")
    assert 3 <= len(consultas) <= 8
    assert any("Linear" in c for c in consultas) and any("Stripe" in c for c in consultas)
    assert len(set(consultas)) == len(consultas)
    assert all(len(c) <= 500 for c in consultas)


def _png(botao=(15, 118, 110)):
    img = Image.new("RGB", (768, 600), (255, 255, 255))
    ImageDraw.Draw(img).rectangle([300, 250, 470, 300], fill=botao)
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _buscar_falso(chamadas):
    def buscar(query, platform="web", mode="standard", limit=10, image_quality="optimized"):
        chamadas.append((query, platform, mode, limit))
        base = abs(hash(query)) % 10000
        return {"screens": [
            {"id": f"s{base}-{i}", "app_name": "Linear", "platform": "web", "mobbin_url": f"https://mobbin.com/screens/{base}-{i}",
             "image": {"url": f"https://img/{base}-{i}.webp"}} for i in range(3)
        ]}
    return buscar


def test_montar_referencias_grava_so_tokens_e_links(tmp_path):
    chamadas = []
    res = referencias.montar_referencias(str(tmp_path), DIRECAO, "comercio",
                                         buscar=_buscar_falso(chamadas), baixar=lambda url: _png())
    assert res["origem"] == "mobbin_api"
    assert all(modo == "standard" for _, _, modo, _ in chamadas)
    dados = json.loads((tmp_path / "referencias-ui.json").read_text(encoding="utf-8"))
    bruto = json.dumps(dados)
    assert "https://img/" not in bruto  # nunca guarda a URL (nem os bytes) da imagem
    assert all(t["mobbin_url"].startswith("https://mobbin.com/") for t in dados["telas"])
    assert dados["consultas"] and dados["tokens"]["cores"]["light"]["primary"].startswith("#")
    assert dados["direitos"]


def test_segunda_execucao_reusa_o_cache_sem_nova_chamada(tmp_path):
    chamadas = []
    buscar = _buscar_falso(chamadas)
    referencias.montar_referencias(str(tmp_path), DIRECAO, "comercio", buscar=buscar, baixar=lambda url: _png())
    primeiras = len(chamadas)
    assert primeiras >= 3
    referencias.montar_referencias(str(tmp_path), DIRECAO, "comercio", buscar=buscar, baixar=lambda url: _png())
    assert len(chamadas) == primeiras
    assert any((tmp_path / ".aidd" / "cache" / "mobbin").glob("*.json"))


def test_falha_do_mobbin_cai_na_spec_com_aviso_registrado(tmp_path, capsys):
    def buscar(*a, **k):
        raise mobbin_client.MobbinError("Mobbin respondeu 401")
    res = referencias.montar_referencias(str(tmp_path), DIRECAO, "comercio", buscar=buscar, baixar=lambda u: _png())
    assert res["origem"] == "spec"
    assert "401" in res["aviso"]
    dados = json.loads((tmp_path / "referencias-ui.json").read_text(encoding="utf-8"))
    assert dados["origem"] == "spec" and dados["aviso"]
    assert "[AVISO]" in capsys.readouterr().err


def test_origem_spec_nao_chama_o_mobbin(tmp_path):
    res = referencias.montar_referencias(str(tmp_path), DIRECAO, "comercio", usar_mobbin=False)
    assert res["origem"] == "spec"
    dados = json.loads((tmp_path / "referencias-ui.json").read_text(encoding="utf-8"))
    assert dados["direcao_visual"]["referencias"] == ["Linear", "Stripe"]


def test_caminho_mcp_le_o_arquivo_gravado_pelo_harness(tmp_path):
    (tmp_path / ".aidd" / "intake").mkdir(parents=True)
    (tmp_path / ".aidd" / "intake" / "referencias-mcp.json").write_text(json.dumps({
        "fonte": "mcp",
        "telas": [{"id": "t1", "app_name": "Deel", "mobbin_url": "https://mobbin.com/screens/t1"}],
        "fluxos": [{"id": "f1", "name": "Criar pedido", "app_name": "Shopify", "screen_count": 14}],
    }), encoding="utf-8")
    res = referencias.montar_referencias(str(tmp_path), DIRECAO, "comercio", origem_mcp=True)
    assert res["origem"] == "mcp"
    dados = json.loads((tmp_path / "referencias-ui.json").read_text(encoding="utf-8"))
    assert dados["fluxos"][0]["name"] == "Criar pedido"
    assert dados["telas"][0]["id"] == "t1"


def test_caminho_mcp_sem_arquivo_cai_na_spec_com_aviso(tmp_path):
    res = referencias.montar_referencias(str(tmp_path), DIRECAO, "comercio", origem_mcp=True)
    assert res["origem"] == "spec" and "referencias-mcp.json" in res["aviso"]
