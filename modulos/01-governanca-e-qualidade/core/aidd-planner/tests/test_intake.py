# -*- coding: utf-8 -*-
"""Intake do planner (ETAPA_09, Ticket 2 da ETAPA_05): grill e spec antes do `planner init`.

A cadeia canônica é /aidd-grill -> /aidd-spec -> /aidd-planner. O planner só abre com
`.aidd/intake/grill.md` (com as perguntas visuais) e `.aidd/intake/spec.md` válidos pelas CLIs reais,
e a spec traz um bloco `Visual Direction` (tom, cor_primaria, referencias, publico) que alimenta o
DESIGN-SYSTEM.json. Execuções autônomas (sem usuário no chat) são marcadas com `--modo autonomo`.
"""
import hashlib
import json
import os
import shutil
import sys

import pytest

_PLANNER_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PLANNER_DIR not in sys.path:
    sys.path.insert(0, _PLANNER_DIR)

_RAIZ = _PLANNER_DIR
while os.path.dirname(_RAIZ) != _RAIZ and not os.path.isfile(os.path.join(_RAIZ, "ecossistema.py")):
    _RAIZ = os.path.dirname(_RAIZ)
if _RAIZ not in sys.path:
    sys.path.insert(0, _RAIZ)

from src.core_planner import ambiente, intake
from src.cli import main as cli_main

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "intake")

DEPLOY_OK = {
    "VPS_HOST": "203.0.113.10", "VPS_USER": "root", "SSH_KEY_PATH": "/chaves/id_ed25519",
    "CLOUDFLARE_API_TOKEN": "cf-token-de-teste", "CLOUDFLARE_ZONE_ID": "a" * 32,  # pragma: allowlist secret
    "DEFAULT_ROOT_DOMAIN": "exemplo.com.br",
}


@pytest.fixture
def pasta(tmp_path, monkeypatch):
    """Projeto com Ambiente já registrado; o intake é que cada teste monta."""
    monkeypatch.setattr(ambiente, "carregar_env", lambda: dict(DEPLOY_OK))
    assert cli_main(["ambiente", "--pasta", str(tmp_path), "--mobbin", "3"]) == 0
    return tmp_path


def _copiar(pasta, grill=True, spec=True):
    destino = pasta / ".aidd" / "intake"
    destino.mkdir(parents=True, exist_ok=True)
    if grill:
        shutil.copy(os.path.join(FIXTURES, "grill.md"), destino / "grill.md")
    if spec:
        shutil.copy(os.path.join(FIXTURES, "spec.md"), destino / "spec.md")
    return destino


def _argv_init(pasta):
    return ["init", "--fluxo", "1", "--nome", "Controle de Pedidos", "--slug", "controle-pedidos",
            "--descricao", "Sistema web de pedidos para pequenos comercios", "--dominio", "comercio",
            "--ui-ref", "deterministico", "--pasta", str(pasta)]


# --- verificação -------------------------------------------------------------------------------------

def test_sem_grill_e_sem_spec_reprova_e_cita_as_skills_e_os_caminhos(pasta):
    erros = intake.verificar(str(pasta))
    texto = "\n".join(erros)
    assert "/aidd-grill" in texto and "/aidd-spec" in texto
    assert os.path.join(".aidd", "intake", "grill.md") in texto
    assert os.path.join(".aidd", "intake", "spec.md") in texto


def test_intake_completo_passa(pasta):
    _copiar(pasta)
    assert intake.verificar(str(pasta)) == []


def test_grill_sem_perguntas_visuais_reprova(pasta):
    destino = _copiar(pasta)
    (destino / "grill.md").write_text(
        "### 1. Qual o escopo?\n- a) pedidos\n\nRecommended: a, porque é o mínimo.\n", encoding="utf-8")
    texto = "\n".join(intake.verificar(str(pasta)))
    for tema in ("tom", "cor", "referências", "público"):
        assert tema in texto


def test_spec_invalida_pela_cli_real_reprova(pasta):
    destino = _copiar(pasta)
    (destino / "spec.md").write_text("# Spec\n\n## 1. Context & Explicit Non-Goals\nso isto\n", encoding="utf-8")
    texto = "\n".join(intake.verificar(str(pasta)))
    assert "spec" in texto.lower() and "validar" in texto.lower()


@pytest.mark.parametrize("trecho,esperado", [
    ("- cor_primaria: #0F766E\n", "cor_primaria"),
    ("- tom: sóbrio e profissional\n", "tom"),
    ("- referencias: Linear, Stripe\n", "referencias"),
    ("- publico: atendentes de pequenos comércios\n", "publico"),
])
def test_spec_sem_item_da_direcao_visual_reprova(pasta, trecho, esperado):
    destino = _copiar(pasta)
    conteudo = (destino / "spec.md").read_text(encoding="utf-8").replace(trecho, "")
    (destino / "spec.md").write_text(conteudo, encoding="utf-8")
    assert esperado in "\n".join(intake.verificar(str(pasta)))


def test_cor_primaria_precisa_ser_hexadecimal(pasta):
    destino = _copiar(pasta)
    conteudo = (destino / "spec.md").read_text(encoding="utf-8").replace("#0F766E", "verde bonito")
    (destino / "spec.md").write_text(conteudo, encoding="utf-8")
    assert "cor_primaria" in "\n".join(intake.verificar(str(pasta)))


def test_ler_direcao_visual_extrai_os_quatro_campos(pasta):
    _copiar(pasta)
    visual = intake.ler_direcao_visual(str(pasta))
    assert visual["tom"] == "sóbrio e profissional"
    assert visual["cor_primaria"] == "#0F766E"
    assert visual["referencias"] == ["Linear", "Stripe"]
    assert visual["publico"] == "atendentes de pequenos comércios"


# --- comando `intake` ---------------------------------------------------------------------------------

def test_comando_intake_grava_o_registro_com_hash_e_modo(pasta):
    destino = _copiar(pasta)
    assert cli_main(["entrevista", "--pasta", str(pasta), "--modo", "autonomo"]) == 0
    dados = json.loads((destino / "intake.json").read_text(encoding="utf-8"))
    assert dados["modo"] == "autonomo"
    assert dados["grill_sha256"] == hashlib.sha256((destino / "grill.md").read_bytes()).hexdigest()
    assert dados["spec_sha256"] == hashlib.sha256((destino / "spec.md").read_bytes()).hexdigest()
    assert dados["direcao_visual"]["cor_primaria"] == "#0F766E"


def test_comando_intake_sem_arquivos_sai_com_1(pasta, capsys):
    assert cli_main(["entrevista", "--pasta", str(pasta), "--modo", "interativo"]) == 1
    assert "/aidd-grill" in capsys.readouterr().err


def test_modo_so_aceita_autonomo_ou_interativo(pasta):
    _copiar(pasta)
    with pytest.raises(SystemExit):
        cli_main(["entrevista", "--pasta", str(pasta), "--modo", "qualquer"])


# --- init -----------------------------------------------------------------------------------------------

def test_init_sem_intake_reprova(pasta, capsys):
    assert cli_main(_argv_init(pasta)) == 1
    assert "/aidd-grill" in capsys.readouterr().err
    assert not (pasta / "PLANNER.json").exists()


def test_init_com_intake_usa_a_cor_da_spec_no_design_system(pasta):
    _copiar(pasta)
    assert cli_main(_argv_init(pasta)) == 0
    ds = json.loads((pasta / "DESIGN-SYSTEM.json").read_text(encoding="utf-8"))
    assert ds["paleta"]["primaria"] == "#0F766E"
    assert ds["dual_mode"]["light"]["primary"] == "#0F766E"
    assert ds["dual_mode"]["dark"]["primary"] == "#0F766E"
    assert "spec" in ds["fonte"]
    assert ds["direcao_visual"]["tom"] == "sóbrio e profissional"


def test_dual_mode_usa_a_primaria_do_catalogo_quando_nao_ha_direcao_visual():
    """Bug achado: `paleta.get("primary")` nunca existe (a chave é `primaria`), então o dual mode
    saía sempre #3b82f6, qualquer que fosse a paleta do projeto."""
    from src.core_planner.design_system import gerar_design_system
    ds = gerar_design_system("App", "app", "descricao longa o bastante", "fintech")
    assert ds["dual_mode"]["light"]["primary"] == ds["paleta"]["primaria"]
    assert ds["dual_mode"]["dark"]["primary"] == ds["paleta"]["primaria"]
    assert ds["paleta"]["primaria"] != "#3b82f6"


# --- referências de UI no init (Ticket 3 da ETAPA_05) ------------------------------------------------

def test_init_sem_mobbin_grava_referencias_pela_spec(pasta):
    _copiar(pasta)
    assert cli_main(_argv_init(pasta)[:-4] + ["--pasta", str(pasta)]) == 0  # sem --ui-ref: usa o ambiente
    refs = json.loads((pasta / "referencias-ui.json").read_text(encoding="utf-8"))
    assert refs["origem"] == "spec"
    assert refs["direcao_visual"]["referencias"] == ["Linear", "Stripe"]
    ds = json.loads((pasta / "DESIGN-SYSTEM.json").read_text(encoding="utf-8"))
    assert ds["referencias_ui"] == {"origem": "spec", "arquivo": "referencias-ui.json"}


def test_init_com_chave_consulta_o_mobbin_por_tela_e_usa_o_cache_na_segunda_vez(tmp_path, monkeypatch):
    import src.core_planner.mobbin_client as mc
    from componentes.compartilhado.mcps.mobbin_mcp import token_extractor as te
    from io import BytesIO
    from PIL import Image, ImageDraw

    monkeypatch.setattr(ambiente, "carregar_env", lambda: {**DEPLOY_OK, "MOBBIN_API_KEY": "x"})
    monkeypatch.setattr(ambiente, "validar_chave_mobbin", lambda env, post=None: (True, "ok"))
    assert cli_main(["ambiente", "--pasta", str(tmp_path), "--mobbin", "2"]) == 0
    _copiar(tmp_path)

    chamadas = []

    def buscar(query, platform="web", mode="standard", limit=10, image_quality="optimized"):
        chamadas.append(query)
        return {"screens": [{"id": f"s{len(chamadas)}-{i}", "app_name": "Linear", "platform": "web",
                             "mobbin_url": "https://mobbin.com/screens/x", "image": {"url": "u"}} for i in range(2)]}

    img = Image.new("RGB", (768, 600), (255, 255, 255))
    ImageDraw.Draw(img).rectangle([300, 250, 470, 300], fill=(15, 118, 110))
    buf = BytesIO()
    img.save(buf, format="PNG")
    monkeypatch.setattr(mc, "executar_busca", buscar)
    monkeypatch.setattr(te, "_baixar_padrao", lambda url: buf.getvalue())

    argv = _argv_init(tmp_path)[:-4] + ["--pasta", str(tmp_path)]
    assert cli_main(argv + ["--force"]) == 0
    refs = json.loads((tmp_path / "referencias-ui.json").read_text(encoding="utf-8"))
    assert refs["origem"] == "mobbin_api" and len(chamadas) >= 3
    primeiras = len(chamadas)
    assert cli_main(argv + ["--force"]) == 0
    assert len(chamadas) == primeiras  # cache
    ds = json.loads((tmp_path / "DESIGN-SYSTEM.json").read_text(encoding="utf-8"))
    assert ds["paleta"]["primaria"] == "#0F766E"  # a cor decidida na spec vence a extraída
    assert ds["referencias_ui"]["origem"] == "mobbin_api"
