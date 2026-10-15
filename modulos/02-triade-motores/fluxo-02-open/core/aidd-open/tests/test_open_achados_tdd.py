# -*- coding: utf-8 -*-
"""
Testes TDD de reprodução dos 3 achados do motor AIDD-Open (RED -> GREEN).

Achado #1: Mismatch entre slug do ticket/plano e diretório da fatia vertical gerada
  - Quando um ticket especifica modulo="Atendimento" e slug="tickets", a fatia era
    gerada em src/modules/atendimento/ enquanto o C3 registrava src/modules/tickets/,
    deixando a pasta do C3 vazia (sha256 = e3b0c44...).

Achado #2: Falha em runtime HTTP ao acessar /openapi.json
  - server.py invocava registry.get_openapi_schema(suite_name, "1.0.0"), método inexistente
    em RouteRegistry (que implementa generate_openapi_json).

Achado #3: Falha em runtime HTTP com rotas dinâmicas e estáticas
  - server.py invocava registry.match(method, path), método inexistente em RouteRegistry,
    quebrando o roteamento de endpoints dinâmicos (ex: /api/<slug>, /api/<slug>/<int:id>).
"""
import os
import sys
import json
import tempfile
import urllib.request
import threading
import time
from pathlib import Path
import pytest

_HERE = Path(__file__).resolve().parent
_OPEN_ROOT = _HERE.parent

def _achar_raiz_repo() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "ecossistema.py").is_file():
            return parent
    return Path(__file__).resolve().parents[4]

_REPO_ROOT = _achar_raiz_repo()
_OPEN_MOLDES = _REPO_ROOT / "componentes" / "compartilhado" / "moldes" / "quarteto" / "variantes" / "aidd-open"

for p in (str(_OPEN_MOLDES), str(_REPO_ROOT), str(_OPEN_ROOT), str(_OPEN_ROOT / "src")):
    if p not in sys.path:
        sys.path.insert(0, p)

from core_open import vsa_generator
from openapi import RouteRegistry


class TestAchado1SlugMismatch:
    """Garante que a fatia vertical seja gerada no diretório exato do slug definido no ticket/plano."""

    def test_gerar_fatias_verticais_usa_slug_exato_do_ticket(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dados_plano = {
                "tickets": [
                    {
                        "id": "TCK-01",
                        "ferramenta_destino": "aidd-open",
                        "entrada": {
                            "modulo": "Atendimento ao Cliente",
                            "slug": "tickets",
                            "entidades": ["Ticket"],
                        },
                    }
                ]
            }

            slices = vsa_generator.gerar_fatias_verticais(tmpdir, dados_plano)
            assert len(slices) == 1
            s = slices[0]
            assert s["slice_nome"] == "tickets"
            assert s["caminho_src"] == "src/modules/tickets"

            # O diretório no disco DEVE ser src/modules/tickets, NUNCA atendimento_ao_cliente
            pasta_esperada = Path(tmpdir) / "src" / "modules" / "tickets"
            assert pasta_esperada.is_dir(), f"Pasta esperada não existe: {pasta_esperada}"
            assert (pasta_esperada / "models.py").is_file()
            assert (pasta_esperada / "routes.py").is_file()

            # O sha256_arvore não pode ser o hash de diretório vazio
            assert s["sha256_arvore"] != ("e3b0c44298fc1c14" + "9afbf4c8996fb92427ae41e4649b934ca495991b7852b855")  # pragma: allowlist secret


class TestAchados2e3RouteRegistryCompatibilidadeERuntime:
    """Garante que RouteRegistry possua get_openapi_schema e match para suporte integral ao server modular."""

    def test_route_registry_possui_metodo_get_openapi_schema(self):
        import openapi
        print("ARQUIVO OPENAPI:", openapi.__file__)
        reg = RouteRegistry()
        # Deve ter o método get_openapi_schema compatível com o chamado em server.py
        assert hasattr(reg, "get_openapi_schema"), "RouteRegistry não possui get_openapi_schema"
        schema = reg.get_openapi_schema("Minha Suite", "1.0.0")
        assert isinstance(schema, dict)
        assert schema.get("openapi") == "3.1.0"
        assert schema.get("info", {}).get("title") == "Minha Suite"

    def test_route_registry_match_rotas_estaticas_e_dinamicas(self):
        reg = RouteRegistry()
        reg.routes["GET"] = {}
        reg.routes["POST"] = {}
        reg.routes["PUT"] = {}
        reg.routes["DELETE"] = {}

        @reg.get("/api/tickets")
        def listar(params=None):
            return [{"id": 1, "titulo": "Bug"}]

        @reg.get("/api/tickets/<int:id>")
        def obter(item_id, params=None):
            return {"id": item_id, "titulo": f"Item {item_id}"}

        # 1. Match em rota exata / estática
        match, handler, route_params = reg.match("GET", "/api/tickets")
        assert match is True
        assert route_params == {}
        assert handler() == [{"id": 1, "titulo": "Bug"}]

        # 2. Match em rota dinâmica com parâmetro <int:id>
        match, handler, route_params = reg.match("GET", "/api/tickets/42")
        assert match is True
        assert route_params.get("id") == 42
        assert handler(route_params["id"]) == {"id": 42, "titulo": "Item 42"}

        # 3. Match não encontrado
        match, handler, route_params = reg.match("GET", "/api/inexistente")
        assert match is False
        assert handler is None
        assert route_params == {}
