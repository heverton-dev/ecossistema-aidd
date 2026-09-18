# -*- coding: utf-8 -*-
"""
Testes de src/core/nextjs_exporter.py (Lei Inviolável #11: Padrão-Ouro de
Stack Tecnológica). Cobertura real, sem mock: gera o frontend contra um
projeto AIDD de verdade (via `compose_suite()`) e, no teste "de fogo",
efetivamente roda `npm install && npm run build` — nunca confiar só em
checagem estática de arquivo (mesmo padrão de rigor já usado nesta sessão
para o backend Python: ver `test_compose_suite.py::test_servidor_gerado_sobe_e_responde`).
"""

import json
import os
import shutil
import subprocess
import sys

import pytest

SCRIPTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
SRC_CORE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src", "core"))
for p in (SCRIPTS_DIR, SRC_CORE_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

NPM_DISPONIVEL = shutil.which("npm") is not None


@pytest.fixture
def suite_composta(tmp_path):
    from compose_suite import compose_suite
    target = tmp_path / "suite-teste"
    compose_suite(str(target), "Suite Teste", ["produtos"])
    return target


@pytest.fixture
def frontend_gerado(suite_composta):
    from nextjs_exporter import NextJSExporter
    frontend_dir = suite_composta / "frontend"
    resultado = NextJSExporter().export_project(str(suite_composta), str(frontend_dir))
    return frontend_dir, resultado


def test_export_descobre_modulos_reais(frontend_gerado):
    _frontend_dir, resultado = frontend_gerado
    assert "produtos" in resultado["modules"]


def test_export_gera_estrutura_next_app_router(frontend_gerado):
    frontend_dir, _ = frontend_gerado
    assert (frontend_dir / "package.json").is_file()
    assert (frontend_dir / "next.config.js").is_file()
    assert (frontend_dir / "tsconfig.json").is_file()
    assert (frontend_dir / "tailwind.config.ts").is_file()
    assert (frontend_dir / "app" / "layout.tsx").is_file()
    assert (frontend_dir / "app" / "page.tsx").is_file()
    assert (frontend_dir / "app" / "produtos" / "page.tsx").is_file()
    assert (frontend_dir / "Dockerfile").is_file()


def test_package_json_respeita_lei_11_versoes_exatas(frontend_gerado):
    """Lei Inviolável #11: versões exatas de proj_ctt (o padrão-ouro validado)."""
    frontend_dir, _ = frontend_gerado
    pkg = json.loads((frontend_dir / "package.json").read_text(encoding="utf-8"))
    assert pkg["dependencies"]["next"] == "^14.2.5"
    assert pkg["dependencies"]["react"] == "^18.3.1"
    assert pkg["dependencies"]["react-dom"] == "^18.3.1"
    assert pkg["devDependencies"]["typescript"] == "^5.4.5"
    assert pkg["devDependencies"]["tailwindcss"] == "^3.4.4"


def test_next_config_usa_output_standalone(frontend_gerado):
    """Achado real em proj_ctt: sem `output: "standalone"` o Dockerfile
    multi-stage (COPY .next/standalone) não funciona."""
    frontend_dir, _ = frontend_gerado
    conteudo = (frontend_dir / "next.config.js").read_text(encoding="utf-8")
    assert 'output: "standalone"' in conteudo


def test_api_client_usa_uma_unica_env_var(frontend_gerado):
    """Achado real em proj_ctt: duas env vars conflitantes
    (NEXT_PUBLIC_API_URL vs NEXT_PUBLIC_API_BASE_URL) em dois clientes HTTP
    paralelos. Aqui deve haver só um cliente, com um único nome de env var."""
    frontend_dir, _ = frontend_gerado
    conteudo = (frontend_dir / "lib" / "api-client.ts").read_text(encoding="utf-8")
    assert "NEXT_PUBLIC_API_URL" in conteudo
    assert "NEXT_PUBLIC_API_BASE_URL" not in conteudo


def test_paleta_e_dinamica_nao_fixa_entre_projetos(tmp_path):
    """Achado real do usuário (18/09/2026): um design fixo/hardcoded no
    gerador faria todo projeto gerado ter a mesma cara — a identidade
    visual (cor primária) precisa ser única por projeto."""
    from compose_suite import compose_suite
    from nextjs_exporter import NextJSExporter

    alvo_saude = tmp_path / "suite-saude"
    compose_suite(str(alvo_saude), "Clinica Bem Estar", ["produtos"])
    resultado_saude = NextJSExporter().export_project(
        str(alvo_saude), str(alvo_saude / "frontend"), suite_name="Clinica Bem Estar"
    )

    alvo_delivery = tmp_path / "suite-delivery"
    compose_suite(str(alvo_delivery), "Lanchonete Rapida", ["produtos"])
    resultado_delivery = NextJSExporter().export_project(
        str(alvo_delivery), str(alvo_delivery / "frontend"), suite_name="Lanchonete Rapida"
    )

    assert resultado_saude["paleta"]["primaria"] != resultado_delivery["paleta"]["primaria"]

    tw_saude = (alvo_saude / "frontend" / "tailwind.config.ts").read_text(encoding="utf-8")
    tw_delivery = (alvo_delivery / "frontend" / "tailwind.config.ts").read_text(encoding="utf-8")
    assert resultado_saude["paleta"]["primaria"] in tw_saude
    assert resultado_delivery["paleta"]["primaria"] in tw_delivery
    assert resultado_saude["paleta"]["primaria"] not in tw_delivery


def test_le_design_system_json_do_planner_quando_existe(tmp_path):
    """A fonte preferida da paleta é o DESIGN-SYSTEM.json gerado pelo
    aidd-planner (permite customização humana depois) — só cai para o
    catálogo determinístico direto quando o arquivo não existe."""
    import json as _json
    from compose_suite import compose_suite
    from nextjs_exporter import NextJSExporter

    alvo = tmp_path / "suite-custom"
    compose_suite(str(alvo), "Projeto Qualquer", ["produtos"])
    (alvo / "DESIGN-SYSTEM.json").write_text(
        _json.dumps({"paleta": {"nome": "Custom", "primaria": "#123456", "primaria_hover": "#0f2a44", "neutro": "slate"}}),
        encoding="utf-8",
    )

    resultado = NextJSExporter().export_project(str(alvo), str(alvo / "frontend"), suite_name="Projeto Qualquer")
    assert resultado["paleta"]["primaria"] == "#123456"
    tw = (alvo / "frontend" / "tailwind.config.ts").read_text(encoding="utf-8")
    assert "#123456" in tw


def test_gera_pasta_public_para_o_dockerfile_encontrar(frontend_gerado):
    """Achado real: Dockerfile faz `COPY --from=builder /app/public ./public`,
    mas o gerador nunca criava essa pasta — `docker compose build` falhava
    com "/app/public": not found`."""
    frontend_dir, _ = frontend_gerado
    assert (frontend_dir / "public").is_dir()


def test_nao_reimplementa_studios_nativos_do_backend(frontend_gerado):
    """Por design: /docs, /webhooks, /mcp continuam nativos do backend
    Python (roteados pelo Nginx), não duplicados/mockados em React — achado
    real em proj_ctt onde o Next.js mockava esses dados e o Nginx/Traefik
    tornava os HTMLs Python inacessíveis publicamente."""
    frontend_dir, _ = frontend_gerado
    assert not (frontend_dir / "app" / "docs").exists()
    assert not (frontend_dir / "app" / "webhooks").exists()
    assert not (frontend_dir / "app" / "mcp").exists()
    assert not (frontend_dir / "app" / "api").exists()


@pytest.mark.skipif(not NPM_DISPONIVEL, reason="npm não disponível neste ambiente")
def test_npm_install_e_build_funcionam_de_verdade(frontend_gerado):
    """Teste de fogo: o frontend gerado precisa REALMENTE compilar. Sem
    isso, os testes acima poderiam passar com um TSX/JSON malformado."""
    frontend_dir, _ = frontend_gerado

    res_install = subprocess.run(
        ["npm", "install"], cwd=str(frontend_dir),
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=300, shell=(os.name == "nt"),
    )
    assert res_install.returncode == 0, res_install.stdout + res_install.stderr

    res_build = subprocess.run(
        ["npm", "run", "build"], cwd=str(frontend_dir),
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=300, shell=(os.name == "nt"),
    )
    assert res_build.returncode == 0, res_build.stdout + res_build.stderr
    assert (frontend_dir / ".next" / "standalone" / "server.js").is_file()
