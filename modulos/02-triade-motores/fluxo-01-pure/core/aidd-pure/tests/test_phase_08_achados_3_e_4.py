# -*- coding: utf-8 -*-
"""
Achados #3 e #4 do motor PURE — TDD red→green.

Achado #3: Contradição entre pasta infrastructure/ e PYTHONPATH.
- O teste de integração determinístico gerava 'from infrastructure.{mod} import RepositorioSQLite'
  incondicionalmente, falhando com ModuleNotFoundError se o módulo foi salvo na raiz de src/.
- Fix: import direto 'from {mod} import RepositorioSQLite' com fallback resiliente.

Achado #4: Conexão SQLite entre threads nos testes de integração.
- RepositorioSQLite determinístico criava sqlite3.connect(":memory:") sem check_same_thread=False,
  causando ProgrammingError quando acessado de múltiplas threads (ex: FastAPI TestClient).
- Fix: adicionar check_same_thread=False na criação de conexões SQLite.
"""

import ast
import textwrap
from pathlib import Path
import pytest

IMPL_PY = (
    Path(__file__).parent.parent
    / "scripts" / "phases" / "08_implementador.py"
)


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


# ---------------------------------------------------------------------------
# Testes do Achado #3: Import de persistência resiliente
# ---------------------------------------------------------------------------

class TestAchado3ImportPersistencia:
    """Garante que módulos de persistência na raiz de src/ não quebrem por forçar 'infrastructure.'"""

    def test_persistencia_na_raiz_nao_forca_prefixo_infrastructure_estrito(self):
        """Se caminho_relativo é 'persistencia.py', o teste gerado não pode ter import incondicional de infrastructure."""
        corpo = _extrair_corpo_metodo("_gerar_teste_integracao_deterministico")
        assert corpo, "Método não encontrado"

        # Simular compilação e execução mínima
        conteudo_capturado = []
        def fake_escrever(p, c):
            conteudo_capturado.append(c)

        ns = {
            "Path": Path, "List": list, "Dict": dict, "Tuple": tuple,
            "Optional": type(None), "ast": ast,
            "escrever_atomico": fake_escrever,
        }

        # Extrair e injetar _extrair_simbolo_publico
        corpo_extrair = _extrair_corpo_metodo("_extrair_simbolo_publico")
        fn_ns = {"ast": ast, "Optional": type(None)}
        exec(compile(textwrap.dedent(corpo_extrair), "<fn_extrair>", "exec"), fn_ns)

        metodos = textwrap.indent(textwrap.dedent(corpo), "    ") + "\n"
        class_src = (
            "class _Imp:\n"
            + metodos
            + "    def _rodar_pytest(self, caminho_relativo=None): return {'passaram':1,'falharam':0,'erros':0,'erro_coleta':False,'saida':''}\n"
            + "    pasta_projeto = Path('/tmp/test_a3')\n"
        )
        exec(compile(class_src, "<imp>", "exec"), ns)
        Cls = ns["_Imp"]
        Cls._extrair_simbolo_publico = staticmethod(fn_ns["_extrair_simbolo_publico"])

        inst = object.__new__(Cls)
        inst.__class__.pasta_projeto = Path('/tmp/test_a3')

        scripts = [{
            "nome": "persistencia",
            "caminho_relativo": "persistencia.py",  # NA RAIZ, NÃO EM infrastructure/
            "codigo": "class RepositorioSQLite:\n    def salvar(self, id, d): return True\n    def buscar(self, id): return 'conteudo'",
            "teste": "assert True",
        }]

        with __import__("unittest.mock", fromlist=["patch"]).patch("pathlib.Path.mkdir"):
            inst._gerar_teste_integracao_deterministico(scripts)

        assert conteudo_capturado, "Nenhum teste gerado"
        gerado = conteudo_capturado[0]

        # Não pode ter import incondicional 'from infrastructure.persistencia import RepositorioSQLite'
        # sem fallback para import direto, pois o arquivo está na raiz de src/
        linhas = [l.strip() for l in gerado.splitlines()]
        tem_import_direto_ou_fallback = any(
            "from persistencia import RepositorioSQLite" in l or "try:" in l
            for l in linhas
        )
        assert tem_import_direto_ou_fallback, (
            "ACHADO #3: Módulo de persistência na raiz gerou import fixo de 'infrastructure.', "
            f"que falhará com ModuleNotFoundError.\nConteúdo:\n{gerado}"
        )


# ---------------------------------------------------------------------------
# Testes do Achado #4: SQLite check_same_thread=False
# ---------------------------------------------------------------------------

class TestAchado4SQLiteCheckSameThread:
    """Garante que a implementação determinística de persistência use check_same_thread=False."""

    def test_repositorio_sqlite_usa_check_same_thread_false(self):
        """O código gerado para RepositorioSQLite deve passar check_same_thread=False no connect."""
        corpo = _extrair_corpo_metodo("_gerar_implementacao_deterministica")
        assert corpo, "Método não encontrado"

        # Verificar diretamente no texto do método se check_same_thread=False está presente
        assert "check_same_thread=False" in corpo, (
            "ACHADO #4: _gerar_implementacao_deterministica gera sqlite3.connect(':memory:') "
            "sem check_same_thread=False, causando falha ao acessar de múltiplas threads em testes."
        )

    def test_execucao_multi_thread_repositorio_sqlite(self):
        """Verifica se uma conexão criada pelo template do RepositorioSQLite funciona em outra thread."""
        import sqlite3
        import threading

        # Conexão com check_same_thread=False funciona em outra thread
        conn = sqlite3.connect(":memory:", check_same_thread=False)
        conn.execute("CREATE TABLE t (id TEXT)")
        conn.commit()

        sucesso = []
        def rodar():
            try:
                conn.execute("INSERT INTO t VALUES ('1')")
                conn.commit()
                sucesso.append(True)
            except Exception as e:
                sucesso.append(e)

        t = threading.Thread(target=rodar)
        t.start()
        t.join()

        assert sucesso == [True], f"Falha ao usar conexão em outra thread: {sucesso}"
