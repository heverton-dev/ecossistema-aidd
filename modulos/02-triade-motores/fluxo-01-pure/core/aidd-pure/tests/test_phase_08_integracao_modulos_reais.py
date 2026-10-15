# -*- coding: utf-8 -*-
"""
Achado #2 do motor PURE — TDD red→green.

Garante que o teste de integração gerado pela Fase 8 produza
asserções reais para QUALQUER nome de módulo, não apenas para
nomes contendo keywords genéricas (validador/servico/persistencia/quarteto).

Antes do fix: módulos com nomes arbitrários (ex: gerenciador_tarefas,
processador_pedidos) caem no else → linhas_chamadas vazia → assert True.
Após  o fix : todo módulo implementado recebe ao menos uma asserção real
derivada do que foi gerado (função pública ou classe).

Estratégia de isolamento: extraímos _gerar_teste_integracao_deterministico
do AST do arquivo fonte e reexecutamos em namespace mínimo — evita a cadeia
de imports de utils_delegacao, escritor_atomico, utils_modelo, etc.
"""

import ast
import textwrap
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# Extração via AST
# ---------------------------------------------------------------------------

IMPL_PY = (
    Path(__file__).parent.parent
    / "scripts" / "phases" / "08_implementador.py"
)

SCRIPTS_GENERICOS = [
    ("gerenciador_tarefas.py",  "nome arbitrário sem keyword"),
    ("processador_pedidos.py",  "nome de domínio real"),
    ("exportador_relatorio.py", "módulo de exportação"),
    ("agendador.py",            "nome curto sem keyword"),
]

SCRIPTS_KEYWORDS = [
    ("validadores.py",  "keyword: validador"),
    ("servico_core.py", "keyword: servico"),
    ("persistencia.py", "keyword: persistencia"),
    ("quarteto_api.py", "keyword: quarteto"),
]


def _extrair_corpo_metodo(nome_metodo: str) -> str:
    """Retorna o source do método como string, dedentado para nível 0."""
    src = IMPL_PY.read_text(encoding="utf-8")
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == nome_metodo:
            trecho = ast.get_source_segment(src, node)
            if trecho:
                return textwrap.dedent(trecho)
    return ""


@pytest.fixture(scope="module")
def classe_minima():
    """
    Constrói uma classe mínima contendo
    _extrair_simbolo_publico + _gerar_teste_integracao_deterministico
    + stub de _rodar_pytest, executada em namespace isolado.
    """
    corpo_gerar = _extrair_corpo_metodo("_gerar_teste_integracao_deterministico")
    corpo_extrair = _extrair_corpo_metodo("_extrair_simbolo_publico")

    if not corpo_gerar:
        pytest.skip("Método _gerar_teste_integracao_deterministico não encontrado em 08_implementador.py")

    conteudo_capturado: list = []

    def fake_escrever_atomico(path, conteudo):
        conteudo_capturado.append(conteudo)

    ns = {
        "Path": Path,
        "List": list,
        "Dict": dict,
        "Tuple": tuple,
        "Optional": type(None),
        "ast": ast,
        "staticmethod": staticmethod,
        "escrever_atomico": fake_escrever_atomico,
        "_conteudo_capturado": conteudo_capturado,
    }

    # Compilar _extrair_simbolo_publico como função livre no namespace
    fn_extrair = None
    if corpo_extrair:
        fn_ns: dict = {"ast": ast, "Optional": type(None)}
        exec(compile(textwrap.dedent(corpo_extrair), "<fn_extrair>", "exec"), fn_ns)
        fn_extrair = fn_ns.get("_extrair_simbolo_publico")

    metodos = textwrap.indent(textwrap.dedent(corpo_gerar), "    ") + "\n"

    class_src = (
        "class _ImplementadorMinimo:\n"
        + metodos
        + "    def _rodar_pytest(self, caminho_relativo=None):\n"
        + "        return {'passaram':1,'falharam':0,'erros':0,'erro_coleta':False,'saida':''}\n"
        + "    pasta_projeto = Path('/tmp/pure_achado2')\n"
    )

    exec(compile(class_src, "<achado2_minimo>", "exec"), ns)
    Cls = ns["_ImplementadorMinimo"]

    # Injetar _extrair_simbolo_publico como staticmethod após exec
    if fn_extrair is not None:
        Cls._extrair_simbolo_publico = staticmethod(fn_extrair)

    return Cls, conteudo_capturado


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fazer_scripts(nomes):
    return [
        {
            "nome": Path(n).stem,
            "caminho_relativo": n,
            "caminho_teste": f"test_{n}",
            "codigo": "def executar(): return True",
            "teste": f"from {Path(n).stem} import executar\ndef test_ok(): assert executar()",
            "tentativas": 1,
        }
        for n in nomes
    ]


def _gerar_conteudo(classe_minima, nomes):
    Cls, capturado = classe_minima
    capturado.clear()
    inst = object.__new__(Cls)
    # garante que pasta_projeto existe no namespace da instância
    inst.__class__.pasta_projeto = Path("/tmp/pure_achado2")

    with __import__("unittest.mock", fromlist=["patch"]).patch("pathlib.Path.mkdir"):
        inst._gerar_teste_integracao_deterministico(_fazer_scripts(nomes))

    return capturado[0] if capturado else ""


def _asserções_reais(conteudo: str):
    return [
        l.strip() for l in conteudo.splitlines()
        if l.strip().startswith("assert") and l.strip() != "assert True"
    ]


# ---------------------------------------------------------------------------
# Testes RED (falham antes do fix)
# ---------------------------------------------------------------------------

class TestAchado2ModulosGenericos:
    """Módulos sem keyword → assert True (RED antes do fix)."""

    @pytest.mark.parametrize("nome,desc", SCRIPTS_GENERICOS)
    def test_modulo_arbitrario_nao_produz_apenas_assert_true(self, classe_minima, nome, desc):
        conteudo = _gerar_conteudo(classe_minima, [nome])

        linhas_assert = [
            l.strip() for l in conteudo.splitlines()
            if l.strip().startswith("assert")
        ]
        assert linhas_assert, (
            f"Nenhuma asserção gerada para '{nome}' ({desc})\n"
            f"Conteúdo:\n{conteudo}"
        )
        assert not all(l == "assert True" for l in linhas_assert), (
            f"ACHADO #2 — '{nome}' ({desc}) produziu apenas 'assert True'.\n"
            f"O teste de integração deve gerar asserções reais (não placeholder).\n"
            f"Conteúdo:\n{conteudo}"
        )

    def test_multiplos_modulos_arbitrarios_todos_com_asserções(self, classe_minima):
        nomes = [n for n, _ in SCRIPTS_GENERICOS]
        conteudo = _gerar_conteudo(classe_minima, nomes)
        reais = _asserções_reais(conteudo)
        assert len(reais) >= len(nomes), (
            f"ACHADO #2 — {len(nomes)} módulos arbitrários, apenas {len(reais)} "
            f"asserções reais.\nConteúdo:\n{conteudo}"
        )


class TestAchado2Regressao:
    """Módulos com keyword devem continuar gerando asserções reais (regressão)."""

    @pytest.mark.parametrize("nome,desc", SCRIPTS_KEYWORDS)
    def test_modulo_com_keyword_nao_regride(self, classe_minima, nome, desc):
        conteudo = _gerar_conteudo(classe_minima, [nome])
        linhas_assert = [
            l.strip() for l in conteudo.splitlines()
            if l.strip().startswith("assert")
        ]
        assert linhas_assert, f"Nenhuma asserção para '{nome}' ({desc})"
        assert not all(l == "assert True" for l in linhas_assert), (
            f"REGRESSÃO — '{nome}' ({desc}) regrediu para 'assert True'.\n"
            f"Conteúdo:\n{conteudo}"
        )
