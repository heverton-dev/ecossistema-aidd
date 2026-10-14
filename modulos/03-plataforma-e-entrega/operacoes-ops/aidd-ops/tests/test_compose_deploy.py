# -*- coding: utf-8 -*-
"""Deploy real do `compose-nativo` (único motor; o Coolify foi abolido em 13/10/2026) — ETAPA_10.

O deploy copia o projeto gerado (sem segredos, sem `.git`, sem `node_modules`) para a VPS por SSH e roda
`docker compose up -d --build`, depois confere que todos os serviços subiram. O DNS da borda é criado na
Cloudflare. A infraestrutura é injetada (transporte SSH e HTTP), então o encadeamento é provado sem VPS;
o transporte SSH real (paramiko) e a API real da Cloudflare não foram exercitados contra um servidor de verdade.
"""
import io
import json
import os
import sys
import tarfile

import pytest

TOOL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (TOOL_ROOT, os.path.join(TOOL_ROOT, "scripts"), os.path.join(TOOL_ROOT, "src")):
    if p not in sys.path:
        sys.path.insert(0, p)

from core_ops import compose_deploy, cloudflare_dns
from core_ops.compose_preflight import ComposePreflightValidator, verificar_isolamento_compose


class TransporteFalso:
    def __init__(self, respostas=None):
        self.comandos = []
        self.enviados = []
        self.respostas = respostas or {}

    def executar(self, comando):
        self.comandos.append(comando)
        for trecho, resposta in self.respostas.items():
            if trecho in comando:
                return resposta
        return 0, ""

    def enviar(self, conteudo, destino_remoto):
        self.enviados.append((conteudo, destino_remoto))


@pytest.fixture
def projeto(tmp_path):
    (tmp_path / "docker-compose.yml").write_text("services:\n  api:\n    image: app:1\n", encoding="utf-8")
    (tmp_path / "Dockerfile").write_text("FROM python:3.12\n", encoding="utf-8")
    (tmp_path / ".env").write_text("SEGREDO=nao-pode-subir\n", encoding="utf-8")  # pragma: allowlist secret
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text("x", encoding="utf-8")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "lixo.js").write_text("x", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("print(1)\n", encoding="utf-8")
    return tmp_path


PS_OK = json.dumps([{"Service": "api", "State": "running", "Health": ""}])


def _deployer(transporte):
    return compose_deploy.ComposeDeployer(host="203.0.113.10", transporte=transporte)


# --- pacote enviado ---------------------------------------------------------------------------------------

def test_pacote_exclui_segredos_git_e_dependencias(projeto):
    nomes = compose_deploy.listar_arquivos_do_pacote(str(projeto))
    assert "docker-compose.yml" in nomes and "src/app.py" in nomes
    for proibido in (".env", ".git/config", "node_modules/lixo.js"):
        assert proibido not in nomes


def test_deploy_envia_o_tar_sem_o_env_e_sobe_com_compose(projeto):
    transporte = TransporteFalso({"compose ps": (0, PS_OK)})
    res = _deployer(transporte).deploy(str(projeto), "clinicas")
    assert res.sucesso, res.erro
    conteudo, destino = transporte.enviados[0]
    assert destino.startswith("/opt/aidd/clinicas/")
    with tarfile.open(fileobj=io.BytesIO(conteudo), mode="r:gz") as tar:
        nomes = tar.getnames()
    assert ".env" not in nomes and "docker-compose.yml" in nomes
    comandos = " | ".join(transporte.comandos)
    assert "mkdir -p /opt/aidd/clinicas" in comandos
    assert "docker compose up -d --build" in comandos
    assert comandos.index("mkdir -p") < comandos.index("tar -xzf") < comandos.index("up -d --build") < comandos.index("compose ps")


def test_falha_do_compose_up_vira_resultado_de_erro_com_o_final_do_log(projeto):
    transporte = TransporteFalso({"up -d --build": (1, "linha1\nERRO: build quebrou\n")})
    res = _deployer(transporte).deploy(str(projeto), "clinicas")
    assert not res.sucesso and res.codigo == "COMPOSE_UP_FALHOU"
    assert "build quebrou" in json.dumps(res.detalhes)


def test_servico_fora_do_ar_reprova_o_deploy(projeto):
    ps = json.dumps([{"Service": "api", "State": "running", "Health": ""},
                     {"Service": "db", "State": "exited", "Health": ""}])
    res = _deployer(TransporteFalso({"compose ps": (0, ps)})).deploy(str(projeto), "clinicas")
    assert not res.sucesso and res.codigo == "SERVICO_NAO_SAUDAVEL"
    assert "db" in json.dumps(res.detalhes)


def test_servico_unhealthy_tambem_reprova(projeto):
    ps = json.dumps([{"Service": "api", "State": "running", "Health": "unhealthy"}])
    res = _deployer(TransporteFalso({"compose ps": (0, ps)})).deploy(str(projeto), "clinicas")
    assert not res.sucesso and res.codigo == "SERVICO_NAO_SAUDAVEL"


@pytest.mark.parametrize("ambiente", ["a b", "x; rm -rf /", "../fora", "$(id)", ""])
def test_nome_de_ambiente_inseguro_e_recusado_sem_tocar_na_vps(projeto, ambiente):
    transporte = TransporteFalso()
    res = _deployer(transporte).deploy(str(projeto), ambiente)
    assert not res.sucesso and res.codigo == "AMBIENTE_INVALIDO"
    assert transporte.comandos == [] and transporte.enviados == []


def test_projeto_sem_compose_nao_chega_na_vps(tmp_path):
    transporte = TransporteFalso()
    res = _deployer(transporte).deploy(str(tmp_path), "clinicas")
    assert not res.sucesso and res.codigo == "COMPOSE_AUSENTE"
    assert transporte.comandos == []


def test_dry_run_devolve_o_plano_sem_tocar_na_vps(projeto):
    transporte = TransporteFalso()
    res = compose_deploy.ComposeDeployer(host="203.0.113.10", transporte=transporte, dry_run=True).deploy(
        str(projeto), "clinicas")
    assert res.sucesso and res.valor["dry_run"] is True
    assert "docker compose up -d --build" in " ".join(res.valor["comandos"])
    assert transporte.comandos == [] and transporte.enviados == []


# --- isolamento (NIH #21, agora sobre o compose) --------------------------------------------------------------

def test_isolamento_aceita_80_e_443_e_portas_altas():
    yaml_ok = "services:\n  proxy:\n    image: nginx:1\n    ports: ['80:80', '443:443']\n  api:\n    image: a:1\n    ports: ['8000:8000']\n"
    assert verificar_isolamento_compose(yaml_ok) == []


def test_isolamento_reprova_porta_privilegiada_do_host_fora_de_80_e_443():
    yaml_ruim = "services:\n  db:\n    image: postgres:16\n    ports: ['22:5432']\n"
    erros = verificar_isolamento_compose(yaml_ruim)
    assert len(erros) == 1 and "db" in erros[0] and "22" in erros[0]


def test_o_lint_do_compose_continua_funcionando():
    ok, erros = ComposePreflightValidator.validate_compose_content("services:\n  a:\n    image: x:1\n")
    assert ok and erros == []


# --- Cloudflare (DNS da borda) -----------------------------------------------------------------------------------

class HttpFalso:
    def __init__(self, registros=None, status=200):
        self.chamadas = []
        self.registros = registros or []
        self.status = status

    def __call__(self, metodo, url, corpo=None, headers=None):
        self.chamadas.append((metodo, url, corpo, headers))
        if metodo == "GET":
            return self.status, {"success": self.status == 200, "result": self.registros, "errors": []}
        return self.status, {"success": self.status == 200, "result": {"id": "novo"}, "errors": []}


def test_dns_cria_o_registro_a_quando_nao_existe():
    http = HttpFalso()
    res = cloudflare_dns.garantir_registro_a("tok-secreto", "z" * 32, "app.exemplo.com.br", "203.0.113.10", http=http)  # pragma: allowlist secret
    assert res.sucesso and res.valor["acao"] == "criado"
    metodos = [c[0] for c in http.chamadas]
    assert metodos == ["GET", "POST"]
    corpo = http.chamadas[1][2]
    assert corpo["type"] == "A" and corpo["name"] == "app.exemplo.com.br" and corpo["content"] == "203.0.113.10"


def test_dns_atualiza_quando_o_ip_mudou_e_nao_mexe_quando_igual():
    existente = [{"id": "r1", "type": "A", "name": "app.exemplo.com.br", "content": "198.51.100.7"}]
    http = HttpFalso(existente)
    res = cloudflare_dns.garantir_registro_a("t", "z" * 32, "app.exemplo.com.br", "203.0.113.10", http=http)
    assert res.sucesso and res.valor["acao"] == "atualizado"
    assert [c[0] for c in http.chamadas] == ["GET", "PUT"]
    igual = HttpFalso([{"id": "r1", "type": "A", "name": "app.exemplo.com.br", "content": "203.0.113.10"}])
    res2 = cloudflare_dns.garantir_registro_a("t", "z" * 32, "app.exemplo.com.br", "203.0.113.10", http=igual)
    assert res2.valor["acao"] == "inalterado" and [c[0] for c in igual.chamadas] == ["GET"]


def test_dns_erro_da_api_vira_resultado_sem_vazar_o_token():
    res = cloudflare_dns.garantir_registro_a("tok-secreto", "z" * 32, "app.exemplo.com.br", "203.0.113.10",  # pragma: allowlist secret
                                             http=HttpFalso(status=403))
    assert not res.sucesso and res.codigo == "DNS_API_FALHOU"
    assert "tok-secreto" not in json.dumps(res.detalhes) + (res.erro or "")


def test_dns_dry_run_nao_chama_a_api():
    http = HttpFalso()
    res = cloudflare_dns.garantir_registro_a("t", "z" * 32, "app.exemplo.com.br", "203.0.113.10", http=http, dry_run=True)
    assert res.sucesso and res.valor["dry_run"] is True and http.chamadas == []


def test_dns_valida_o_nome_e_o_ip():
    assert cloudflare_dns.garantir_registro_a("t", "z" * 32, "nome invalido!", "203.0.113.10", http=HttpFalso()).codigo == "DNS_ENTRADA_INVALIDA"
    assert cloudflare_dns.garantir_registro_a("t", "z" * 32, "app.exemplo.com.br", "nao-e-ip", http=HttpFalso()).codigo == "DNS_ENTRADA_INVALIDA"
