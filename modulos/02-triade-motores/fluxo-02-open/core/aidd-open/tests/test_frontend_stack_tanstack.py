# -*- coding: utf-8 -*-
"""Frontend do aidd-open: padrão-ouro TanStack Router + Vite (Lei #11); Next.js abolido.

Cobre o validador da fase 09, o gate G_FACTORY_INTEGRATION e o gerador VSA.
"""
import importlib.util
import json
import os
import sys
import tempfile

import pytest

_FACTORY_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
for _p in (os.path.join(_FACTORY_ROOT, "src"), os.path.join(_FACTORY_ROOT, "scripts"),
           os.path.join(_FACTORY_ROOT, "scripts", "phases_open")):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def _carregar(caminho: str, nome: str):
    spec = importlib.util.spec_from_file_location(nome, caminho)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


@pytest.fixture(scope="module")
def fase09():
    return _carregar(os.path.join(_FACTORY_ROOT, "scripts", "phases_open", "09_integracao.py"), "fase09_integracao")


@pytest.fixture(scope="module")
def gate():
    return _carregar(os.path.join(_FACTORY_ROOT, "gates", "G_FACTORY_INTEGRATION.py"), "g_factory_integration")


def _projeto(tmp, dependencias, arquivos=()):
    os.makedirs(os.path.join(tmp, "src"), exist_ok=True)
    with open(os.path.join(tmp, "src", "server.py"), "w", encoding="utf-8") as f:
        f.write("x = 1\n")
    os.makedirs(os.path.join(tmp, "frontend"), exist_ok=True)
    with open(os.path.join(tmp, "frontend", "package.json"), "w", encoding="utf-8") as f:
        json.dump({"name": "f", "dependencies": dependencias}, f)
    for rel in arquivos:
        caminho = os.path.join(tmp, "frontend", *rel.split("/"))
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        open(caminho, "w", encoding="utf-8").close()
    return tmp


ARQUIVOS_TANSTACK = ("vite.config.ts", "tsconfig.json", "index.html", "src/main.tsx", "src/router.tsx")


def _problemas_frontend(problemas):
    return [p for p in problemas if "rontend" in p or "Front-end" in p]


@pytest.mark.parametrize("quem", ["fase09", "gate"])
def test_frontend_com_next_e_reprovado_como_abolido(quem, fase09, gate):
    validar = fase09._validar_vsa if quem == "fase09" else gate._validar_integracao
    with tempfile.TemporaryDirectory() as tmp:
        _projeto(tmp, {"next": "^14.2.5", "react": "^18.3.1"})
        achados = _problemas_frontend(validar(tmp))
    assert any("abolido" in p for p in achados), achados


@pytest.mark.parametrize("quem", ["fase09", "gate"])
def test_frontend_tanstack_incompleto_e_reprovado(quem, fase09, gate):
    validar = fase09._validar_vsa if quem == "fase09" else gate._validar_integracao
    with tempfile.TemporaryDirectory() as tmp:
        _projeto(tmp, {"@tanstack/react-router": "^1.81.0"}, arquivos=("package.json.keep",))
        achados = _problemas_frontend(validar(tmp))
    assert any("TanStack incompleto" in p for p in achados), achados


@pytest.mark.parametrize("quem", ["fase09", "gate"])
def test_frontend_tanstack_completo_passa(quem, fase09, gate):
    validar = fase09._validar_vsa if quem == "fase09" else gate._validar_integracao
    with tempfile.TemporaryDirectory() as tmp:
        _projeto(tmp, {"@tanstack/react-router": "^1.81.0"}, arquivos=ARQUIVOS_TANSTACK)
        achados = _problemas_frontend(validar(tmp))
    assert achados == [], achados


def test_vsa_generator_rejeita_stack_nextjs_abolida():
    from core_open.vsa_generator import gerar_aplicacao_vsa

    analysis = {"nicho_slug": "clinicas", "nicho_nome_exibicao": "Clínicas", "ferramentas": [{"nome": "Typebot"}]}
    with tempfile.TemporaryDirectory() as tmp:
        res = gerar_aplicacao_vsa(analysis, tmp, frontend_stack="nextjs")
        assert not res.sucesso
        assert "frontend_stack" in str(res.erro)
        assert not os.path.isfile(os.path.join(tmp, "src", "server.py"))
