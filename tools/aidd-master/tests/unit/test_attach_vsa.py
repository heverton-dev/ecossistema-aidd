# -*- coding: utf-8 -*-
"""
Testes para `master attach-vsa` (Etapa 4 do FLUXO 03: conectar o backend VSA
a um frontend low-code preservado pelo aidd-bridge, sem sobrescrever o
Dockerfile/docker-compose.yml/Caddyfile/frontend que ja existem).

Contexto do bug de arquitetura que este comando resolve: `aidd-master init`
sempre gera seu proprio Dockerfile/docker-compose.yml/frontend (Next.js por
padrao, Lei #11) na raiz do projeto -- rodar isso direto em cima da saida do
aidd-bridge destruiria a stack Docker (web/db/postgrest/storage/caddy) e o
frontend original ja validados. `attach-vsa` faz so a parte que falta:
backend isolado em backend/ + servico "api" mesclado no compose/Caddyfile
existentes.
"""

import os
import subprocess
import sys

import pytest
import yaml

SCRIPTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)


def _cria_saida_bridge_falsa(tmp_path):
    """Fixture minima que imita o que o aidd-bridge realmente deixa no
    diretorio de saida: frontend na raiz (package.json, src/pages/...),
    Dockerfile do frontend, docker-compose.yml (web/db/postgrest/storage/caddy)
    e Caddyfile modo localhost -- sem depender do aidd-bridge estar instalado."""
    project_dir = tmp_path / "projeto-bridge"
    (project_dir / "src" / "pages").mkdir(parents=True)
    (project_dir / "src" / "pages" / "Index.tsx").write_text("export default function Index(){}", encoding="utf-8")
    (project_dir / "package.json").write_text('{"name": "gestao-tarefas-lovable"}', encoding="utf-8")
    (project_dir / "Dockerfile").write_text("FROM node:20-alpine AS builder\n", encoding="utf-8")

    compose = {
        "services": {
            "web": {"build": {"context": ".", "dockerfile": "Dockerfile"}, "expose": ["80"]},
            "db": {"image": "postgres:16-alpine"},
            "postgrest": {"image": "postgrest/postgrest:latest"},
        },
        "volumes": {"postgres_data": None},
    }
    (project_dir / "docker-compose.yml").write_text(yaml.safe_dump(compose, sort_keys=False), encoding="utf-8")

    caddyfile = """localhost {
    handle_path /rest/v1/* {
        reverse_proxy postgrest:3000
    }

    handle_path /storage/v1/* {
        reverse_proxy storage:5000
    }

    handle {
        reverse_proxy web:80
    }
}
"""
    (project_dir / "Caddyfile").write_text(caddyfile, encoding="utf-8")
    return project_dir


def test_provision_backend_only_nao_toca_arquivos_do_frontend_preservado(tmp_path):
    from provision_project import provision_backend_only

    project_dir = _cria_saida_bridge_falsa(tmp_path)
    frontend_index_antes = (project_dir / "src" / "pages" / "Index.tsx").read_text(encoding="utf-8")
    dockerfile_antes = (project_dir / "Dockerfile").read_text(encoding="utf-8")

    resultado = provision_backend_only(str(project_dir), "tarefas", "Modulo de tarefas")

    # Frontend original intocado
    assert (project_dir / "src" / "pages" / "Index.tsx").read_text(encoding="utf-8") == frontend_index_antes
    assert (project_dir / "Dockerfile").read_text(encoding="utf-8") == dockerfile_antes
    assert (project_dir / "package.json").read_text(encoding="utf-8") == '{"name": "gestao-tarefas-lovable"}'

    # Backend isolado em backend/, nao em src/ da raiz
    backend_dir = project_dir / "backend"
    assert (backend_dir / "src" / "server.py").is_file()
    assert (backend_dir / "src" / "modules" / "tarefas").is_dir()
    assert not (project_dir / "src" / "server.py").exists()
    assert resultado["backend_dir"] == str(backend_dir)


def test_provision_backend_only_usa_paleta_do_design_system_da_raiz(tmp_path):
    """Reproduz bug real: provision_backend_only() passava `backend_dir` (o
    subdiretorio isolado do backend) como `project_dir` pra
    generate_modular_server_code(), mas DESIGN-SYSTEM.json (gerado pelo
    aidd-planner, Lei #11) vive na RAIZ do projeto -- resolver_paleta_projeto
    nunca achava o arquivo, caia no fallback por hash, e os Estudios nativos
    (Swagger/Webhooks/MCP) saiam com uma cor diferente da que o frontend
    preservado ja usa (two-tone mismatch)."""
    from provision_project import provision_backend_only

    project_dir = _cria_saida_bridge_falsa(tmp_path)
    (project_dir / "DESIGN-SYSTEM.json").write_text(
        '{"paleta": {"nome": "Rosa Padrao", "primaria": "#E11D48", "primaria_hover": "#BE123C", "neutro": "slate"}}',
        encoding="utf-8",
    )

    provision_backend_only(str(project_dir), "tarefas")

    server_code = (project_dir / "backend" / "src" / "server.py").read_text(encoding="utf-8")
    assert "#E11D48" in server_code, "server.py nao usou a paleta real do DESIGN-SYSTEM.json da raiz do projeto"


def test_provision_backend_only_renderiza_docs_html_sem_placeholder_cru(tmp_path):
    """Reproduz bug real (achado com Playwright de verdade no navegador):
    /docs/guia servia o MOLDE cru de docs.html sem processar o Jinja2 --
    o browser recebia `const SPOTLIGHT_COMMANDS = {{ spotlight_commands }};`
    literal, o que e JS invalido (SyntaxError: Unexpected token '{'),
    quebrando a pagina inteira. provision_backend_only() fazia so um
    shutil.copyfile() do template cru, sem chamar generate_documentation_html()
    (que o compose_suite.py, usado por outro fluxo, ja fazia corretamente)."""
    from provision_project import provision_backend_only

    project_dir = _cria_saida_bridge_falsa(tmp_path)
    provision_backend_only(str(project_dir), "tarefas")

    docs_html = (project_dir / "backend" / "src" / "static" / "docs.html").read_text(encoding="utf-8")
    assert "{{ spotlight_commands }}" not in docs_html
    assert "{{" not in docs_html and "}}" not in docs_html

    import subprocess
    import sys
    import re

    scripts = re.findall(r"<script[^>]*>(.*?)</script>", docs_html, re.S)
    for script in scripts:
        script_path = tmp_path / "_check.js"
        script_path.write_text(script, encoding="utf-8")
        resultado = subprocess.run(["node", "--check", str(script_path)], capture_output=True, text=True)
        assert resultado.returncode == 0, f"JS invalido em docs.html: {resultado.stderr}"


def test_provision_backend_only_server_py_importa_de_verdade(tmp_path):
    """Mesma disciplina do teste equivalente de provision(): nao basta o
    arquivo existir, ele precisa importar sem ModuleNotFoundError."""
    from provision_project import provision_backend_only

    project_dir = _cria_saida_bridge_falsa(tmp_path)
    provision_backend_only(str(project_dir), "tarefas")

    resultado = subprocess.run(
        [sys.executable, "-c", "import server"],
        cwd=str(project_dir / "backend" / "src"),
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=15,
    )
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr


def test_attach_infra_mescla_servico_api_sem_apagar_servicos_existentes(tmp_path):
    from attach_vsa_infra import attach_infra

    project_dir = _cria_saida_bridge_falsa(tmp_path)
    resultado = attach_infra(str(project_dir))
    assert resultado["conectado"] is True

    with open(project_dir / "docker-compose.yml", encoding="utf-8") as f:
        compose = yaml.safe_load(f)

    assert set(["web", "db", "postgrest", "api"]).issubset(compose["services"].keys())
    assert compose["services"]["web"]["expose"] == ["80"]  # servico original intocado
    assert compose["services"]["api"]["build"]["dockerfile"] == "Dockerfile.api"

    assert (project_dir / "Dockerfile.api").is_file()
    dockerfile_api = (project_dir / "Dockerfile.api").read_text(encoding="utf-8")
    assert "COPY backend/requirements.txt" in dockerfile_api
    assert "COPY --chown=aidduser:aiddgroup backend/src/" in dockerfile_api


def test_attach_infra_roteia_quarteto_no_caddyfile_antes_do_catchall(tmp_path):
    from attach_vsa_infra import attach_infra

    project_dir = _cria_saida_bridge_falsa(tmp_path)
    attach_infra(str(project_dir))

    caddyfile = (project_dir / "Caddyfile").read_text(encoding="utf-8")
    for path in ["/docs*", "/webhooks*", "/mcp*", "/metrics*", "/openapi.json", "/health", "/static/*", "/api/*"]:
        assert path in caddyfile, f"rota {path} nao foi mesclada no Caddyfile"

    # As rotas do Quarteto precisam vir ANTES do catch-all do frontend,
    # senao o catch-all "handle {}" engole tudo primeiro (Caddy usa a
    # primeira "handle" que casar).
    pos_docs = caddyfile.index("/docs*")
    pos_catchall = caddyfile.index("reverse_proxy web:80")
    assert pos_docs < pos_catchall

    # rotas ja existentes do bridge continuam intactas
    assert "handle_path /rest/v1/*" in caddyfile
    assert "handle_path /storage/v1/*" in caddyfile


def test_attach_infra_e_idempotente(tmp_path):
    """Rodar attach-vsa duas vezes nao pode duplicar as rotas no Caddyfile."""
    from attach_vsa_infra import attach_infra

    project_dir = _cria_saida_bridge_falsa(tmp_path)
    attach_infra(str(project_dir))
    attach_infra(str(project_dir))

    caddyfile = (project_dir / "Caddyfile").read_text(encoding="utf-8")
    assert caddyfile.count("/docs*") == 1


def test_attach_infra_sem_bridge_previo_nao_faz_nada(tmp_path):
    """Um projeto puro do Fluxo 01/02 (sem docker-compose.yml/Caddyfile
    previos) nao deve ter nada mesclado -- ele ja gera seu proprio Docker
    via `master init`."""
    from attach_vsa_infra import attach_infra

    project_dir = tmp_path / "projeto-puro"
    project_dir.mkdir()

    resultado = attach_infra(str(project_dir))
    assert resultado["conectado"] is False
    assert not (project_dir / "Dockerfile.api").exists()


def test_cmd_attach_vsa_end_to_end(tmp_path):
    import types
    from application.commands.attach_vsa import cmd_attach_vsa

    project_dir = _cria_saida_bridge_falsa(tmp_path)
    cmd_attach_vsa(types.SimpleNamespace(nome="tarefas", descricao="Modulo de tarefas", dir=str(project_dir)))

    assert (project_dir / "backend" / "src" / "server.py").is_file()
    assert (project_dir / "Dockerfile.api").is_file()
    with open(project_dir / "docker-compose.yml", encoding="utf-8") as f:
        compose = yaml.safe_load(f)
    assert "api" in compose["services"]
    caddyfile = (project_dir / "Caddyfile").read_text(encoding="utf-8")
    assert "/mcp*" in caddyfile
