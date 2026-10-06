# -*- coding: utf-8 -*-
"""
Teste de integração do Item 08: o scaffold de módulos (compose_suite ->
add_module.py -> templates cookiecutter) DEVE gerar toda fatia vertical com
as 4 camadas da Clean Architecture/DDD (domain/application/infrastructure/
interfaces) já LIMPAS de fábrica pelo gate G_ARQUITETURA_DELIVERABLE.

Cenários cobertos (sem mocks, engine real):
1. Módulo gerado durante a composição inicial da suíte (compose_suite).
2. Módulo adicionado DEPOIS, via comando real `add_module.py` (CLI documentada).

Em ambos, valida:
- Existência das 4 camadas + facades de compatibilidade (models/services/routes);
- G_ARQUITETURA_DELIVERABLE com DIRETORIOS_AUDITADOS escopado ao módulo gerado
  retorna exit 0 (nenhuma violação de Clean Architecture).
"""

import importlib.util
import os
import subprocess
import sys

import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
GATE_PATH = os.path.join(REPO_ROOT, "gates", "G_ARQUITETURA_DELIVERABLE.py")

SCRIPTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

CAMADAS = ("domain", "application", "infrastructure", "interfaces")


@pytest.fixture(scope="module")
def carregar_gate():
    """Carrega o ficheiro do gate G_ARQUITETURA_DELIVERABLE da raiz do
    ecossistema (não o cópia de dentro da suíte gerada)."""
    assert os.path.isfile(GATE_PATH), f"Gate não encontrado em {GATE_PATH}"
    spec = importlib.util.spec_from_file_location("G_ARQUITETURA_DELIVERABLE", GATE_PATH)
    assert spec is not None and spec.loader is not None, f"Não foi possível carregar {GATE_PATH}"
    gate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate)
    return gate


def _executar_gate_no_modulo(gate, target, slug):
    """Roda o gate exclusivamente sobre o módulo gerado '<slug>', ignorando o
    restante do projeto composto (que contém arquivos legados fora do escopo
    Clean Architecture do Item 08)."""
    gate.DIRETORIOS_AUDITADOS = [os.path.join("src", "modules", slug).replace("\\", "/")]
    rc = gate.checar(root_dir=str(target))
    assert rc == 0, (
        f"G_ARQUITETURA_DELIVERABLE reprovou o módulo '{slug}' gerado pelo scaffold "
        f"(exit {rc}). Inspecione as violações acima."
    )


def _assert_camadas_e_facades(target, slug):
    mod_dir = target / "src" / "modules" / slug
    for camada in CAMADAS:
        assert (mod_dir / camada).is_dir(), f"Camada {camada}/ não gerada em {slug}"
        assert (mod_dir / camada / "__init__.py").is_file()

    # peças-chave de cada camada
    assert (mod_dir / "domain" / "entities.py").is_file()
    assert (mod_dir / "domain" / "events.py").is_file()
    assert (mod_dir / "domain" / "repositories.py").is_file()
    assert (mod_dir / "domain" / "value_objects.py").is_file()
    assert (mod_dir / "application" / "use_cases.py").is_file()
    assert (mod_dir / "application" / "dtos.py").is_file()
    assert (mod_dir / "infrastructure" / "schema.py").is_file()
    assert (mod_dir / "infrastructure" / "sqlite_repository.py").is_file()
    assert (mod_dir / "infrastructure" / "outbox.py").is_file()
    assert (mod_dir / "interfaces" / "routes.py").is_file()

    # facades de compatibilidade preservadas (server.py importa modules.<slug>.models/services/routes)
    assert (mod_dir / "models.py").is_file()
    assert (mod_dir / "services.py").is_file()
    assert (mod_dir / "routes.py").is_file()

    # camadas não podem vazar .j2 (todo template deve ser renderizado para .py)
    para_jinja = list((mod_dir / "domain").rglob("*.j2"))
    para_jinja += list((mod_dir / "application").rglob("*.j2"))
    para_jinja += list((mod_dir / "infrastructure").rglob("*.j2"))
    para_jinja += list((mod_dir / "interfaces").rglob("*.j2"))
    assert para_jinja == [], f"Arquivos .j2 não renderizados em {slug}: {para_jinja}"


def test_modulo_da_composicao_inicial_nasce_com_camadas_ddd_e_passa_gate(tmp_path, carregar_gate):
    """Módulo gerado na composição inicial (compose_suite) já sai com as 4
    camadas, facades de compatibilidade e ZERO violação do gate."""
    from compose_suite import compose_suite

    target = tmp_path / "suite-gate-composicao"
    compose_suite(str(target), "Suite Gate Item08", ["scaffoldmod"])

    _assert_camadas_e_facades(target, "scaffoldmod")
    _executar_gate_no_modulo(carregar_gate, target, "scaffoldmod")


def test_modulo_adicionado_apos_composicao_via_add_module_passa_gate(tmp_path, carregar_gate):
    """Módulo adicionado DEPOIS da composição via comando real `add_module.py`
    também nasce com as 4 camadas e passa no gate — cobre o caminho de
    regeração de src/server.py com os templates novos."""
    from compose_suite import compose_suite

    target = tmp_path / "suite-gate-pos-composicao"
    compose_suite(str(target), "Suite Gate Item08", ["crm"])

    resultado = subprocess.run(
        [sys.executable, "scripts/add_module.py", "billing"],
        cwd=str(target),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert resultado.returncode == 0, (
        f"add_module.py falhou ao adicionar 'billing':\n"
        f"stdout: {resultado.stdout}\nstderr: {resultado.stderr}"
    )

    _assert_camadas_e_facades(target, "billing")
    _executar_gate_no_modulo(carregar_gate, target, "billing")

    # server.py regenerado ainda importa as facades do novo módulo (wiring).
    server_src = (target / "src" / "server.py").read_text(encoding="utf-8")
    assert "from modules.billing.models import init_schema" in server_src
    assert "from modules.billing.services import BillingService" in server_src
    assert "from modules.billing.routes import registrar_rotas" in server_src