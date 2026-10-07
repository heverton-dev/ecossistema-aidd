# -*- coding: utf-8 -*-
"""Ticket 4 (ciclo-03 VSA): nada vivo aponta para tools/aidd-* (decisão A: modulos/ é a cópia canônica).

Varre `git ls-files` atrás de `tools/aidd-`, `tools\\aidd-`, `"tools", "aidd-` e `TOOLS_DIR` em
código, configs, gates, testes, skills, harnesses e docs vivos. Fica de fora só o que é
histórico (relatórios, planos, auditorias de ciclos fechados, sessões) e os mapas/livros,
que são regenerados no Ticket 22 (tests/test_mapas_e_livros_em_dia.py).
"""

import re
import subprocess
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]

PADRAO = re.compile(r'tools[/\\]+aidd-|"tools",\s*"aidd-|TOOLS_DIR')

# Em .py, também a pasta tools/ montada por partes: RAIZ / "tools", partes[0] == "tools",
# os.path.join(X, "tools"), glob("tools/*"), startswith("tools/"). "tools/list" e
# "tools/call" são métodos MCP, não pasta.
PADRAO_PY = re.compile(
    r"""/\s*["']tools["']|==\s*["']tools["']|join\([^)\n]*["']tools["']"""
    r"""|["']tools/(?!list|call)[^"'\s]*["']|[=\[]\s*\(?\s*["']tools["']\s*,|\btools/\{"""
)

DOCS_VIVOS = ("docs/padroes/", "docs/protocolos/", "docs/oficiais/")

PREFIXOS_HISTORICOS = (
    "tools/",          # a própria pasta legada (sai no Ticket 5)
    "secoes/",
    ".mimocode/plans/",
)

# Arquivos que falam de tools/ porque o assunto deles é a migração tools -> modulos.
PERMITIDOS = {
    "scripts/reconciliar_copias_vsa.py",
    "tests/test_reconciliar_copias_vsa.py",
    "tests/test_sem_referencia_tools.py",
    "tests/test_tools_extinto.py",
    "modulos/04-nucleo-compartilhado/gates/G_COPIA_UNICA_VSA.py",
    "modulos/04-nucleo-compartilhado/gates/test_g_copia_unica_vsa.py",
    "modulos/04-nucleo-compartilhado/gates/G_MODULO_FRONTEIRA.py",  # detector de referência a tools/
    "modulos/04-nucleo-compartilhado/gates/test_g_modulo_fronteira.py",  # planta a referência para provar que morde
    "MEMORY.md",  # diário histórico do repo
    ".secrets.baseline",  # estado gerado; reescrito pelo comando de baseline (Ticket 9)
    "tests/test_mapas_e_livros_em_dia.py",  # detector de texto velho nos livros
    "tests/test_nomes_padronizados.py",  # detector dos nomes antigos das ferramentas
    "tests/test_micro_gates_fatias_verdes.py",  # afirma que nenhum prefixo começa com tools/
}


def _no_escopo(caminho: str) -> bool:
    if caminho in PERMITIDOS or caminho.startswith(PREFIXOS_HISTORICOS):
        return False
    if caminho.startswith("docs/"):
        return caminho.startswith(DOCS_VIVOS)
    return True


def _referencias():
    saida = subprocess.run(["git", "ls-files", "-z"], cwd=str(RAIZ), capture_output=True, check=True).stdout
    achados = []
    for caminho in saida.decode("utf-8", errors="replace").split("\0"):
        if not caminho or not _no_escopo(caminho):
            continue
        arquivo = RAIZ / caminho
        try:
            texto = arquivo.read_text(encoding="utf-8", errors="replace")
        except (OSError, IsADirectoryError):
            continue
        for numero, linha in enumerate(texto.splitlines(), 1):
            if PADRAO.search(linha) or (caminho.endswith(".py") and PADRAO_PY.search(linha)):
                achados.append(f"{caminho}:{numero}: {linha.strip()[:120]}")
    return achados


def test_nada_vivo_aponta_para_tools():
    achados = _referencias()
    arquivos = sorted({a.split(":", 1)[0] for a in achados})
    assert not achados, f"{len(arquivos)} arquivo(s) ainda apontam para tools/:\n" + "\n".join(achados[:80])


def test_padrao_pega_as_tres_formas():
    assert PADRAO.search("tools/aidd-forge/x.py")
    assert PADRAO.search(r"tools\aidd-pure\y")
    assert PADRAO.search('os.path.join(ROOT, "tools", "aidd-ops")')
    assert PADRAO.search("TOOLS_DIR = ROOT / 'tools'")
    assert not PADRAO.search("modulos/01-governanca-e-qualidade/core/aidd-forge")


def test_padrao_py_pega_pasta_montada_por_partes():
    assert PADRAO_PY.search('pasta = RAIZ / "tools" / nome')
    assert PADRAO_PY.search("if partes[0] == 'tools':")
    assert PADRAO_PY.search('os.path.join(ROOT_DIR, "tools", ferramenta)')
    assert PADRAO_PY.search('RAIZ.glob("tools/*/templates")')
    assert PADRAO_PY.search('pastas_alvo = ["tools", "componentes", "src"]')
    assert PADRAO_PY.search('erros.append(f"README.md ausente em tools/{tool}")')
    assert not PADRAO_PY.search('if method in ("tools/list", "toolsList"):')
    assert not PADRAO_PY.search('res.get("result", {}).get("tools", [])')
