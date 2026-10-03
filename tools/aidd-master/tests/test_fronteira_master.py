# -*- coding: utf-8 -*-
"""Ticket 17 (D1 / DoD 7): aidd-master integra e faz o Quarteto, sem infra.

Regras e fronteiras validadas:
1. `master init` e `compose_suite` NÃO geram infraestrutura (Dockerfile,
   docker-compose.yml, deploy.sh, pasta nginx/): a infraestrutura é de
   responsabilidade exclusiva do `aidd-ops` (Ticket 16).
2. O servidor dinâmico do master atende a rota canônica `/webhook` com HTTP 200,
   mantendo `/webhooks` como apelido compatível (Quarteto Sine Qua Non 4/4).
3. Os moldes do Quarteto e componentes core são obtidos a partir do
   almoxarifado único do ecossistema via `caminho_peca`.
4. O master consome o contrato C3 (HANDOFF_ENGINE_MASTER.json) e grava o contrato
   formal C4 (HANDOFF_MASTER_ENTERPRISE.json) com status HTTP medido e schema válido.
"""

from __future__ import annotations

import json
import os
import shutil
import socket
import sys
import threading
import time
import urllib.request
from http.server import HTTPServer
from pathlib import Path
from typing import Any, Dict

import jsonschema
import pytest

# Configuração de caminhos do ecossistema
ROOT_DIR = Path(__file__).resolve().parents[3]
MASTER_DIR = ROOT_DIR / "tools" / "aidd-master"
FORGE_DIR = ROOT_DIR / "tools" / "aidd-forge"
SPECS_DIR = ROOT_DIR / "componentes" / "compartilhado" / "specs"
CATALOGO_PATH = ROOT_DIR / "componentes" / "compartilhado" / "CATALOGO.json"

for p in (str(ROOT_DIR), str(MASTER_DIR), str(MASTER_DIR / "scripts"), str(FORGE_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

from aidd_forge.core.almoxarifado import caminho_peca
from scripts.provision_project import provision


def _porta_livre() -> int:
    """Encontra uma porta TCP livre no localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def test_master_init_nao_gera_arquivos_de_infra(tmp_path: Path):
    """Garante que master init não gera Dockerfile, docker-compose.yml, deploy.sh nem nginx."""
    projeto_dir = tmp_path / "projeto-teste-sem-infra"
    projeto_dir.mkdir(parents=True, exist_ok=True)

    provision(str(projeto_dir))

    # Fronteira D1: arquivos de infra NÃO pertencem ao master
    arquivos_proibidos = [
        projeto_dir / "Dockerfile",
        projeto_dir / "docker-compose.yml",
        projeto_dir / "deploy.sh",
        projeto_dir / "nginx",
    ]

    for arq in arquivos_proibidos:
        assert not arq.exists(), f"Violação de fronteira: {arq.name} não deve ser gerado pelo aidd-master"


def test_master_servidor_quarteto_webhook_retorna_200(tmp_path: Path):
    """Garante que GET /webhook retorna 200 no servidor gerado pelo master."""
    projeto_dir = tmp_path / "projeto-quarteto"
    projeto_dir.mkdir(parents=True, exist_ok=True)

    provision(str(projeto_dir))

    server_script = projeto_dir / "src" / "server.py"
    assert server_script.exists(), "src/server.py deve ser gerado"

    # Carregar o módulo do servidor gerado em runtime para testar a rota /webhook
    porta = _porta_livre()
    server_dir = str(projeto_dir / "src")
    if server_dir not in sys.path:
        sys.path.insert(0, server_dir)

    import importlib.util
    spec = importlib.util.spec_from_file_location("server_gerado", str(server_script))
    server_mod = importlib.util.module_from_spec(spec)
    
    # Injetar porta de teste
    server_mod.PORT = porta
    spec.loader.exec_module(server_mod)

    # Subir HTTPServer em thread daemon
    handler_cls = getattr(server_mod, "AppHandler", getattr(server_mod, "ModularServerHandler", None))
    assert handler_cls is not None, "AppHandler/ModularServerHandler deve existir no server.py"
    httpd = HTTPServer(("127.0.0.1", porta), handler_cls)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.3)

    try:
        # 1. Rota canônica /webhook
        url_webhook = f"http://127.0.0.1:{porta}/webhook"
        with urllib.request.urlopen(url_webhook, timeout=5) as resp:
            assert resp.status == 200
            conteudo = resp.read().decode("utf-8")
            assert "Webhook Studio" in conteudo or "webhook" in conteudo.lower()

        # 2. Apelido retrocompatível /webhooks
        url_webhooks = f"http://127.0.0.1:{porta}/webhooks"
        with urllib.request.urlopen(url_webhooks, timeout=5) as resp:
            assert resp.status == 200
    finally:
        httpd.shutdown()
        httpd.server_close()


def test_master_busca_moldes_quarteto_no_almoxarifado():
    """Garante que os moldes do Quarteto estão acessíveis via caminho_peca."""
    pecas_quarteto = [
        "moldes/quarteto/swagger.html",
        "moldes/quarteto/webhook_studio.html",
        "moldes/quarteto/mcp_studio.html",
        "moldes/quarteto/docs.html",
    ]
    for peca in pecas_quarteto:
        caminho = caminho_peca(peca)
        assert caminho.exists(), f"Peça {peca} deve existir no almoxarifado"
        assert caminho.is_file(), f"Peça {peca} deve ser um arquivo regular"


def test_master_consome_c3_e_emite_c4_valido(tmp_path: Path):
    """Garante que o master consome C3 e emite o contrato formal C4 com medição HTTP."""
    from scripts.integrador_master import integrar_fatias_e_emitir_c4

    projeto_dir = tmp_path / "projeto-integracao"
    projeto_dir.mkdir(parents=True, exist_ok=True)
    provision(str(projeto_dir))

    # Cria contrato C3 simulando conclusão de engine construtora
    c3_dados = {
        "versao_schema": "1.0.0",
        "origem_engine": "aidd-open",
        "projeto_slug": "projeto-integracao",
        "slices_geradas": [{
            "slice_nome": "faturamento",
            "caminho_src": "src/modules/faturamento",
            "sha256_arvore": "a" * 64,
            "endpoints": [{"rota": "/api/faturamento", "metodo": "GET", "funcao": "listar"}],
            "tabelas_sql": ["faturas"],
        }],
        "artefatos_frontend": {
            "tecnologia": "tanstack_router",
            "paginas_geradas": ["/faturamento"],
            "origem_design": "tailwind_standard",
        },
        "testes_executados": {
            "total": 2, "passaram": 2, "falharam": 0, "zero_stubs": True,
            "relatorio_pytest": {"caminho": "reports/pytest.xml", "exit_code": 0},
        },
        "arquivos_fora_da_zona": [],
    }
    c3_path = projeto_dir / "HANDOFF_ENGINE_MASTER.json"
    c3_path.write_text(json.dumps(c3_dados, indent=2), encoding="utf-8")

    # Executa a integração do master e emissão do C4
    c4_path = integrar_fatias_e_emitir_c4(str(projeto_dir))
    assert Path(c4_path).exists(), "HANDOFF_MASTER_ENTERPRISE.json deve ser gerado"

    c4_dados = json.loads(Path(c4_path).read_text(encoding="utf-8"))

    # Validação do contrato C4 contra o schema oficial
    schema_c4_path = SPECS_DIR / "handoff-master-to-enterprise.schema.json"
    schema_c4 = json.loads(schema_c4_path.read_text(encoding="utf-8"))
    jsonschema.validate(instance=c4_dados, schema=schema_c4)

    # Checar se rotas do Quarteto incluem /webhook com 200
    rotas_medidas = {item["rota"]: item["status_http_medido"] for item in c4_dados["quarteto"]}
    assert "/webhook" in rotas_medidas or "/webhooks" in rotas_medidas
    for rota, status in rotas_medidas.items():
        assert 200 <= status < 400, f"Rota {rota} retornou status inválido: {status}"
