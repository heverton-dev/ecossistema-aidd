# -*- coding: utf-8 -*-
"""
Contrato determinístico do wrapper .githooks/pre-commit: os logs de um
commit precisam ser descritivos e visíveis EM TEMPO REAL para quem está
rodando, não um bloco mudo por minutos seguido de um resultado final.

Achado real: o wrapper rodava `pre_commit run --color never` sem
`--verbose`. Por padrão o pre-commit esconde a saída de cada hook até ele
terminar (só mostra ao vivo com --verbose, ou depois se o hook falhar) --
G_TESTES_REAIS roda pytest de 7 ferramentas (~5min) e parecia travado/mudo
o tempo todo, mesmo já imprimindo progresso real-time internamente.
"""

import os

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HOOK_PATH = os.path.join(REPO_ROOT, ".githooks", "pre-commit")


def _conteudo_hook():
    with open(HOOK_PATH, "r", encoding="utf-8") as f:
        return f.read()


def test_hook_usa_verbose_para_streaming_ao_vivo():
    conteudo = _conteudo_hook()
    assert "--verbose" in conteudo, (
        "sem --verbose o pre-commit esconde a saida de cada gate ate ele terminar "
        "-- gates lentos (G_TESTES_REAIS) parecem travados por minutos"
    )


def test_hook_nao_desliga_cor_explicitamente():
    conteudo = _conteudo_hook()
    assert "--color never" not in conteudo, "cor desligada explicitamente torna PASS/FAIL mais dificil de escanear"


def test_hook_forca_utf8_para_saida_legivel():
    conteudo = _conteudo_hook()
    assert "PYTHONIOENCODING" in conteudo and "utf-8" in conteudo, (
        "sem UTF-8 forcado, prints com acentuacao (PT-BR, maioria dos gates) saem com mojibake "
        "no console padrao do Windows (cp1252)"
    )


def test_hook_mostra_diagnostico_de_arquivos_ao_falhar():
    conteudo = _conteudo_hook()
    assert "git status --short" in conteudo, (
        "ao falhar, o hook precisa mostrar quais arquivos mudaram no working tree "
        "-- diagnostico minimo pra identificar o que travou"
    )
