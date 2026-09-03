import json
from pathlib import Path

import pytest

from aidd_forge.core.universal_injector import UniversalInjector


def _payload(**overrides):
    base = {
        "tipo": "skill",
        "nome": "demo-skill",
        "descricao": "Skill de demonstracao",
        "conteudo": "# Demo\n",
    }
    base.update(overrides)
    return base


@pytest.mark.parametrize(
    "tipo,conteudo",
    [
        ("skill", "# Demo\n"),
        ("mcp", "def handler():\n    return 1\n"),
        ("rule", "Regra real.\n"),
        ("spec", "Spec real.\n"),
        ("roteiro", "Passo a passo real.\n"),
    ],
)
def test_injetar_cada_tipo_com_sucesso(tmp_path: Path, tipo, conteudo):
    resultado = UniversalInjector(tmp_path).injetar(_payload(tipo=tipo, nome=f"demo-{tipo}", conteudo=conteudo))

    assert resultado.ok is True
    assert resultado.materialization is not None
    assert resultado.materialization.dest.exists()


def test_injetar_skill_sincroniza_harness_existente(tmp_path: Path):
    (tmp_path / ".claude").mkdir()

    resultado = UniversalInjector(tmp_path).injetar(_payload())

    assert resultado.ok is True
    assert resultado.harness_sync is not None
    assert resultado.harness_sync.mirrored


def test_injetar_mcp_atualiza_registry(tmp_path: Path):
    resultado = UniversalInjector(tmp_path).injetar(
        _payload(tipo="mcp", nome="demo-mcp", conteudo="def handler():\n    return 1\n")
    )

    registry_path = tmp_path / "aidd_forge" / "mcps" / "registry.json"
    entries = json.loads(registry_path.read_text(encoding="utf-8"))
    assert entries[0]["nome"] == "demo-mcp"


def test_injetar_payload_invalido_nao_toca_disco(tmp_path: Path):
    resultado = UniversalInjector(tmp_path).injetar(_payload(tipo="invalido"))

    assert resultado.ok is False
    assert resultado.materialization is None
    assert not any(tmp_path.iterdir())


def test_injetar_camada_alvo_conflitante_nao_toca_disco(tmp_path: Path):
    resultado = UniversalInjector(tmp_path).injetar(_payload(tipo="rule", nome="demo-rule", camada_alvo=5))

    assert resultado.ok is False
    assert resultado.materialization is None


def test_injetar_conteudo_stub_reporta_erro(tmp_path: Path):
    resultado = UniversalInjector(tmp_path).injetar(_payload(conteudo="pass"))

    assert resultado.ok is False
    assert resultado.errors
