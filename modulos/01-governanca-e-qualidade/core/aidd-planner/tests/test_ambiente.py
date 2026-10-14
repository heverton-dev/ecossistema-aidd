# -*- coding: utf-8 -*-
"""Bloco Ambiente do planner (ETAPA_08, Ticket 1): o planner abre verificando o ambiente.

Regras decididas com o usuário:
  - Mobbin tem 3 caminhos, nesta ordem: 1 = MCP oficial (pelo harness), 2 = chave no .env, 3 = nenhum;
  - a escolha é gravada em `.aidd/ambiente.json`, sem segredo;
  - o Mobbin nunca bloqueia (sem chave, ou fora do ar, só registra aviso);
  - as variáveis de deploy bloqueiam: VPS_HOST, VPS_USER, CLOUDFLARE_API_TOKEN, CLOUDFLARE_ZONE_ID,
    DEFAULT_ROOT_DOMAIN e (SSH_KEY_PATH ou VPS_PASSWORD). O deploy é só compose-nativo (sem Coolify).
"""
import json
import os
import shutil
import sys

import pytest

_PLANNER_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PLANNER_DIR not in sys.path:
    sys.path.insert(0, _PLANNER_DIR)

from src.core_planner import ambiente
from src.cli import main as cli_main

DEPLOY_OK = {
    "VPS_HOST": "203.0.113.10",
    "VPS_USER": "root",
    "SSH_KEY_PATH": "/chaves/id_ed25519",
    "CLOUDFLARE_API_TOKEN": "cf-token-secreto-123",  # pragma: allowlist secret
    "CLOUDFLARE_ZONE_ID": "a" * 32,
    "DEFAULT_ROOT_DOMAIN": "exemplo.com.br",
}
CHAVE_MOBBIN = "mbn_chave_secreta_muito_longa_9876543210"  # pragma: allowlist secret


@pytest.fixture
def env_do_teste(monkeypatch):
    """O CLI lê o ambiente por `ambiente.carregar_env`; o teste controla o que ele enxerga."""
    estado = {}
    monkeypatch.setattr(ambiente, "carregar_env", lambda: dict(estado))
    return estado


def _argv_init(pasta):
    return ["init", "--fluxo", "1", "--nome", "App Amb", "--slug", "app-amb",
            "--descricao", "Descricao do projeto de teste do ambiente", "--dominio", "fintech",
            "--ui-ref", "deterministico", "--pasta", str(pasta)]


# --- detecção de harness ------------------------------------------------------------------------

@pytest.mark.parametrize("env,esperado", [
    ({"CLAUDECODE": "1"}, "claude-code"),
    ({"OPENCODE_SESSION": "x"}, "opencode"),
    ({"MIMO_HOME": "x"}, "mimocode"),
    ({"ANTIGRAVITY_SESSION": "x"}, "antigravity"),
    ({"GEMINI_CLI": "1"}, "gemini-cli"),
    ({}, "desconhecido"),
])
def test_detecta_harness_pelo_ambiente(env, esperado):
    assert ambiente.detectar_harness(env) == esperado


def test_passo_a_passo_mostra_so_o_do_harness_detectado():
    texto = "\n".join(ambiente.passo_a_passo_mcp("claude-code"))
    assert "claude mcp add" in texto
    assert "https://api.mobbin.com/mcp" in texto
    assert "opencode" not in texto.lower()
    desconhecido = "\n".join(ambiente.passo_a_passo_mcp("desconhecido"))
    assert "https://api.mobbin.com/mcp" in desconhecido


# --- variáveis de deploy ---------------------------------------------------------------------------

def test_deploy_completo_nao_falta_nada():
    assert ambiente.variaveis_deploy_faltando(DEPLOY_OK) == []


def test_deploy_lista_exatamente_o_que_falta():
    faltando = ambiente.variaveis_deploy_faltando({"VPS_HOST": "x"})
    assert set(faltando) == {"VPS_USER", "CLOUDFLARE_API_TOKEN", "CLOUDFLARE_ZONE_ID",
                             "DEFAULT_ROOT_DOMAIN", "SSH_KEY_PATH ou VPS_PASSWORD"}


def test_autenticacao_ssh_aceita_chave_ou_senha():
    sem_chave = {k: v for k, v in DEPLOY_OK.items() if k != "SSH_KEY_PATH"}
    assert ambiente.variaveis_deploy_faltando(sem_chave) == ["SSH_KEY_PATH ou VPS_PASSWORD"]
    assert ambiente.variaveis_deploy_faltando({**sem_chave, "VPS_PASSWORD": "senha"}) == []  # pragma: allowlist secret


def test_valor_em_branco_conta_como_ausente():
    assert ambiente.variaveis_deploy_faltando({**DEPLOY_OK, "VPS_HOST": "   "}) == ["VPS_HOST"]


def test_coolify_nao_e_exigido():
    nomes = " ".join(ambiente.VARIAVEIS_DEPLOY_OBRIGATORIAS)
    assert "COOLIFY" not in nomes.upper()


# --- comando `ambiente` e bloqueio do `init` ------------------------------------------------------

def test_init_sem_ambiente_registrado_reprova_e_lista_os_tres_caminhos(tmp_path, env_do_teste, capsys):
    env_do_teste.update(DEPLOY_OK)
    assert cli_main(_argv_init(tmp_path)) == 1
    err = capsys.readouterr().err
    assert "1" in err and "MCP" in err
    assert "2" in err and "MOBBIN_API_KEY" in err
    assert "3" in err and "nenhum" in err.lower()
    assert err.index("MCP") < err.index("MOBBIN_API_KEY") < err.lower().index("nenhum")
    assert not (tmp_path / "PLANNER.json").exists()


def test_comando_ambiente_grava_escolha_sem_segredos(tmp_path, env_do_teste):
    env_do_teste.update(DEPLOY_OK)
    env_do_teste["MOBBIN_API_KEY"] = CHAVE_MOBBIN
    rc = cli_main(["ambiente", "--pasta", str(tmp_path), "--mobbin", "3"])
    assert rc == 0
    arquivo = tmp_path / ".aidd" / "ambiente.json"
    bruto = arquivo.read_text(encoding="utf-8")
    dados = json.loads(bruto)
    assert dados["mobbin"]["caminho"] == "nenhum"
    assert "harness" in dados
    for segredo in (CHAVE_MOBBIN, DEPLOY_OK["CLOUDFLARE_API_TOKEN"], DEPLOY_OK["VPS_HOST"],
                    DEPLOY_OK["SSH_KEY_PATH"]):
        assert segredo not in bruto


def test_init_passa_depois_de_registrar_o_ambiente(tmp_path, env_do_teste):
    env_do_teste.update(DEPLOY_OK)
    assert cli_main(["ambiente", "--pasta", str(tmp_path), "--mobbin", "3"]) == 0
    destino = tmp_path / ".aidd" / "intake"
    destino.mkdir(parents=True)
    for nome in ("grill.md", "spec.md"):
        shutil.copy(os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "intake", nome), destino / nome)
    assert cli_main(_argv_init(tmp_path)) == 0
    assert (tmp_path / "PLANNER.json").is_file()


def test_deploy_incompleto_bloqueia_o_comando_ambiente_e_o_init(tmp_path, env_do_teste, capsys):
    env_do_teste.update({"VPS_HOST": "203.0.113.10"})
    assert cli_main(["ambiente", "--pasta", str(tmp_path), "--mobbin", "3"]) == 1
    err = capsys.readouterr().err
    for nome in ("VPS_USER", "CLOUDFLARE_API_TOKEN", "CLOUDFLARE_ZONE_ID", "DEFAULT_ROOT_DOMAIN"):
        assert nome in err
    assert "VPS_HOST" not in err.replace("VPS_HOST=", "")  # o que existe não é cobrado
    assert cli_main(_argv_init(tmp_path)) == 1


def test_o_valor_de_nenhuma_variavel_aparece_na_saida(tmp_path, env_do_teste, capsys):
    env_do_teste.update(DEPLOY_OK)
    env_do_teste["MOBBIN_API_KEY"] = CHAVE_MOBBIN
    cli_main(["ambiente", "--pasta", str(tmp_path), "--mobbin", "2"])
    saida = capsys.readouterr()
    texto = saida.out + saida.err
    assert CHAVE_MOBBIN not in texto
    assert CHAVE_MOBBIN[:4] not in texto
    assert DEPLOY_OK["CLOUDFLARE_API_TOKEN"] not in texto


# --- Mobbin nunca bloqueia ------------------------------------------------------------------------

def test_mobbin_chave_ausente_registra_aviso_e_nao_bloqueia(tmp_path, env_do_teste, capsys):
    env_do_teste.update(DEPLOY_OK)
    assert cli_main(["ambiente", "--pasta", str(tmp_path), "--mobbin", "2"]) == 0
    dados = json.loads((tmp_path / ".aidd" / "ambiente.json").read_text(encoding="utf-8"))
    assert dados["mobbin"]["caminho"] == "chave"
    assert dados["mobbin"]["validado"] is False
    assert "MOBBIN_API_KEY" in capsys.readouterr().err


def test_mobbin_chave_valida_e_confirmada_por_chamada_real_minima(monkeypatch):
    chamadas = []

    def post_falso(url, headers=None, json=None, timeout=None):
        chamadas.append((url, json))

        class R:
            status_code = 200
        return R()

    ok, _ = ambiente.validar_chave_mobbin({"MOBBIN_API_KEY": CHAVE_MOBBIN}, post=post_falso)
    assert ok is True
    assert len(chamadas) == 1
    assert chamadas[0][0].endswith("/v1/screens/search")
    assert chamadas[0][1]["limit"] == 1 and chamadas[0][1]["mode"] == "standard"


def test_mobbin_chave_recusada_vira_false_sem_excecao():
    def post_falso(url, headers=None, json=None, timeout=None):
        class R:
            status_code = 401
        return R()

    ok, motivo = ambiente.validar_chave_mobbin({"MOBBIN_API_KEY": CHAVE_MOBBIN}, post=post_falso)
    assert ok is False and CHAVE_MOBBIN not in motivo


def test_mobbin_fora_do_ar_nao_levanta_excecao():
    def post_falso(url, headers=None, json=None, timeout=None):
        raise OSError("rede fora")

    ok, _ = ambiente.validar_chave_mobbin({"MOBBIN_API_KEY": CHAVE_MOBBIN}, post=post_falso)
    assert ok is False


def test_caminho_mcp_e_registrado_sem_validar(tmp_path, env_do_teste, capsys):
    env_do_teste.update(DEPLOY_OK)
    env_do_teste["CLAUDECODE"] = "1"
    assert cli_main(["ambiente", "--pasta", str(tmp_path), "--mobbin", "1"]) == 0
    dados = json.loads((tmp_path / ".aidd" / "ambiente.json").read_text(encoding="utf-8"))
    assert dados["mobbin"]["caminho"] == "mcp"
    assert dados["mobbin"]["validado"] is None
    assert dados["harness"] == "claude-code"
    assert "claude mcp add" in capsys.readouterr().out


def test_ambiente_json_corrompido_ou_com_caminho_invalido_bloqueia_o_init(tmp_path, env_do_teste):
    env_do_teste.update(DEPLOY_OK)
    (tmp_path / ".aidd").mkdir()
    (tmp_path / ".aidd" / "ambiente.json").write_text('{"mobbin": {"caminho": "inventado"}}', encoding="utf-8")
    assert cli_main(_argv_init(tmp_path)) == 1
