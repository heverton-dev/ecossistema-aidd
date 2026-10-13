# -*- coding: utf-8 -*-
"""
Testes de src/core/tanstack_exporter.py (Lei Inviolável #11: Padrão-Ouro de
Stack Tecnológica — TanStack Router + Vite, SPA estática, sem Next.js).
Cobertura real, sem mock: gera o frontend contra um projeto AIDD de verdade
(via `compose_suite()`) e, no teste "de fogo", efetivamente roda
`npm install && npm run build` — nunca confiar só em checagem estática.
Portado dos 11 testes do antigo exportador Next.js, mais as garantias de que
nada de Next.js sobrou e de que o Docker serve um build estático.
"""

import json
import os
import re
import shutil
import subprocess
import sys

import pytest

SCRIPTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
SRC_CORE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src", "core"))
for p in (SCRIPTS_DIR, SRC_CORE_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

NPM_DISPONIVEL = bool(shutil.which("npm") and shutil.which("node"))

# Qualquer rastro do framework abolido em arquivo gerado reprova.
PADRAO_NEXT = re.compile(r"next\.?js|next/|NEXT_PUBLIC|\.next\b|eslint-config-next|next\.config|\"next\"", re.IGNORECASE)


@pytest.fixture
def suite_composta(tmp_path):
    from compose_suite import compose_suite
    target = tmp_path / "suite-teste"
    compose_suite(str(target), "Suite Teste", ["produtos"])
    return target


@pytest.fixture
def frontend_gerado(suite_composta):
    from tanstack_exporter import TanStackRouterExporter
    frontend_dir = suite_composta / "frontend-tanstack"
    resultado = TanStackRouterExporter().export_project(str(suite_composta), str(frontend_dir))
    return frontend_dir, resultado


def test_export_descobre_modulos_reais(frontend_gerado):
    _frontend_dir, resultado = frontend_gerado
    assert "produtos" in resultado["modules"]


def test_export_gera_estrutura_tanstack_vite(frontend_gerado):
    frontend_dir, _ = frontend_gerado
    for rel in (
        "package.json", "vite.config.ts", "tsconfig.json", "tailwind.config.ts", "postcss.config.js",
        "index.html", "Dockerfile", "nginx.conf",
        "src/main.tsx", "src/router.tsx", "src/index.css",
        "src/routes/index.tsx", "src/routes/produtos.tsx",
    ):
        assert (frontend_dir / rel).is_file(), rel


def test_package_json_tanstack_vite_sem_next(frontend_gerado):
    """Lei #11: React 18, TanStack Router, Vite, TypeScript e Tailwind 3; nada de Next."""
    frontend_dir, _ = frontend_gerado
    pkg = json.loads((frontend_dir / "package.json").read_text(encoding="utf-8"))
    deps, dev = pkg["dependencies"], pkg["devDependencies"]
    assert deps["react"] == "^18.3.1"
    assert deps["react-dom"] == "^18.3.1"
    assert "@tanstack/react-router" in deps
    assert "vite" in dev and "typescript" in dev and "tailwindcss" in dev
    assert dev["tailwindcss"].startswith("^3.4")
    assert "next" not in deps and "next" not in dev and "eslint-config-next" not in dev
    assert pkg["scripts"]["build"].endswith("vite build")


def test_build_estatico_em_dist_e_dockerfile_nginx(frontend_gerado):
    """O Dockerfile precisa servir o build estático (dist) por nginx; sem servidor Node."""
    frontend_dir, _ = frontend_gerado
    vite = (frontend_dir / "vite.config.ts").read_text(encoding="utf-8")
    assert 'outDir: "dist"' in vite
    docker = (frontend_dir / "Dockerfile").read_text(encoding="utf-8")
    assert "nginx" in docker and "/app/dist" in docker
    assert "node server.js" not in docker and "standalone" not in docker
    nginx = (frontend_dir / "nginx.conf").read_text(encoding="utf-8")
    assert "try_files $uri /index.html" in nginx


def test_healthcheck_usa_ipv4_explicito(frontend_gerado):
    """Achado real (teste com container): `wget http://localhost:3000` no busybox resolve ::1 e o
    nginx escuta só em IPv4, então o container ficava `unhealthy` (Connection refused)."""
    frontend_dir, _ = frontend_gerado
    docker = (frontend_dir / "Dockerfile").read_text(encoding="utf-8")
    linhas = [l for l in docker.splitlines() if "wget" in l]
    assert linhas, "healthcheck com wget ausente"
    assert all("127.0.0.1" in l and "localhost" not in l for l in linhas), linhas


def test_api_client_usa_uma_unica_env_var(frontend_gerado):
    """Um único cliente HTTP e um único nome de variável de ambiente."""
    frontend_dir, _ = frontend_gerado
    conteudo = (frontend_dir / "src" / "lib" / "api-client.ts").read_text(encoding="utf-8")
    assert "VITE_API_URL" in conteudo
    assert "VITE_API_BASE_URL" not in conteudo


def test_paleta_e_dinamica_nao_fixa_entre_projetos(tmp_path):
    """A identidade visual (cor primária) precisa ser única por projeto."""
    from compose_suite import compose_suite
    from tanstack_exporter import TanStackRouterExporter

    alvo_saude = tmp_path / "suite-saude"
    compose_suite(str(alvo_saude), "Clinica Bem Estar", ["produtos"])
    resultado_saude = TanStackRouterExporter().export_project(
        str(alvo_saude), str(alvo_saude / "frontend-tanstack"), suite_name="Clinica Bem Estar"
    )

    alvo_delivery = tmp_path / "suite-delivery"
    compose_suite(str(alvo_delivery), "Lanchonete Rapida", ["produtos"])
    resultado_delivery = TanStackRouterExporter().export_project(
        str(alvo_delivery), str(alvo_delivery / "frontend-tanstack"), suite_name="Lanchonete Rapida"
    )

    assert resultado_saude["paleta"]["primaria"] != resultado_delivery["paleta"]["primaria"]
    tw_saude = (alvo_saude / "frontend-tanstack" / "tailwind.config.ts").read_text(encoding="utf-8")
    tw_delivery = (alvo_delivery / "frontend-tanstack" / "tailwind.config.ts").read_text(encoding="utf-8")
    assert resultado_saude["paleta"]["primaria"] in tw_saude
    assert resultado_delivery["paleta"]["primaria"] in tw_delivery
    assert resultado_saude["paleta"]["primaria"] not in tw_delivery


def test_le_design_system_json_do_planner_quando_existe(tmp_path):
    """Fonte preferida da paleta: DESIGN-SYSTEM.json do aidd-planner."""
    from compose_suite import compose_suite
    from tanstack_exporter import TanStackRouterExporter

    alvo = tmp_path / "suite-custom"
    compose_suite(str(alvo), "Projeto Qualquer", ["produtos"])
    (alvo / "DESIGN-SYSTEM.json").write_text(
        json.dumps({"paleta": {"nome": "Custom", "primaria": "#123456", "primaria_hover": "#0f2a44", "neutro": "slate"}}),
        encoding="utf-8",
    )
    resultado = TanStackRouterExporter().export_project(
        str(alvo), str(alvo / "frontend-tanstack"), suite_name="Projeto Qualquer"
    )
    assert resultado["paleta"]["primaria"] == "#123456"
    assert "#123456" in (alvo / "frontend-tanstack" / "tailwind.config.ts").read_text(encoding="utf-8")


def test_gera_pasta_public_para_o_vite(frontend_gerado):
    frontend_dir, _ = frontend_gerado
    assert (frontend_dir / "public").is_dir()


def test_navbar_linka_os_5_estudios_nativos(frontend_gerado):
    """Os 5 estúdios nativos do backend são links comuns (<a>), servidos pelo Python/nginx."""
    frontend_dir, _ = frontend_gerado
    navbar = (frontend_dir / "src" / "components" / "Navbar.tsx").read_text(encoding="utf-8")
    for destino in ("/docs", "/docs/guia", "/webhooks", "/mcp", "/metrics"):
        assert f'href="{destino}"' in navbar, destino


def test_nao_reimplementa_studios_nativos_do_backend(frontend_gerado):
    frontend_dir, _ = frontend_gerado
    for nome in ("docs", "webhooks", "mcp", "api"):
        assert not (frontend_dir / "src" / "routes" / nome).exists()
        assert not (frontend_dir / "src" / "routes" / f"{nome}.tsx").exists()


def test_nenhum_arquivo_gerado_menciona_next(frontend_gerado):
    """Abolição do Next.js: nenhum rastro em nenhum arquivo gerado."""
    frontend_dir, resultado = frontend_gerado
    achados = []
    for caminho in resultado["files_created"]:
        arquivo = frontend_dir / caminho if not os.path.isabs(caminho) else __import__("pathlib").Path(caminho)
        if arquivo.suffix in (".png", ".ico", ".webp"):
            continue
        texto = arquivo.read_text(encoding="utf-8", errors="replace")
        if PADRAO_NEXT.search(texto):
            achados.append(str(arquivo))
    assert achados == [], achados


def test_inclui_libs_offline_first_do_template_padrao_ouro(frontend_gerado):
    """Offline-first é exigência do padrão-ouro (gate G_TEMPLATE_TANSTACK_OFFLINE)."""
    frontend_dir, _ = frontend_gerado
    for rel in ("src/lib/pwa.ts", "src/lib/seguranca.ts", "src/lib/offline/sync-queue.ts"):
        assert (frontend_dir / rel).is_file(), rel


@pytest.mark.skipif(not NPM_DISPONIVEL, reason="npm não disponível neste ambiente")
def test_npm_install_e_build_funcionam_de_verdade(frontend_gerado):
    """Teste de fogo: o frontend gerado precisa REALMENTE compilar (tsc + vite build)."""
    frontend_dir, _ = frontend_gerado
    npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
    res_install = subprocess.run(
        f"{npm_cmd} install", cwd=str(frontend_dir), capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=600, shell=True,
    )
    assert res_install.returncode == 0, res_install.stdout[-2000:] + res_install.stderr[-2000:]
    res_build = subprocess.run(
        f"{npm_cmd} run build", cwd=str(frontend_dir), capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=600, shell=True,
    )
    assert res_build.returncode == 0, res_build.stdout[-3000:] + res_build.stderr[-2000:]
    assert (frontend_dir / "dist" / "index.html").is_file()
