# -*- coding: utf-8 -*-
"""
Testes do Item 6 — 02-otimizacao-tokenomics-latencia:
mapa de secoes handoff fase 6 -> fase 7.

Criterios de saida do plano:
1. Para 5 documentos >500 linhas cada, mapa consome <= 50% dos tokens do dump bruto.
2. Topicso-chave (requisitos, arquitetura, testes) preservados no mapa.
3. Funcoes auxiliares (_detectar_topicos_chave, _extrair_resumo_executivo) funcionam.
"""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent
_PHASES_DIR = _ROOT / 'scripts' / 'phases'
if str(_PHASES_DIR) not in sys.path:
    sys.path.insert(0, str(_PHASES_DIR))


@pytest.fixture(scope='module')
def mod7():
    spec = importlib.util.spec_from_file_location(
        'p07_analisador_item6', str(_PHASES_DIR / '07_analisador.py')
    )
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def _contar_tokens(texto: str) -> int:
    try:
        import tiktoken
        return len(tiktoken.get_encoding('cl100k_base').encode(texto))
    except Exception:
        return max(len(texto.split()), len(texto) // 4, 1)


def _gerar_documento_extenso(nome_doc: str, total_linhas: int = 550) -> str:
    linhas = [
        f"# Documentacao Completa de {nome_doc}",
        "",
        "Este documento apresenta a especificacao tecnica detalhada do sistema.",
        "A integracao entre todos os modulos garante alta disponibilidade.",
        "",
        "## Requisitos Funcionais e Nao-Funcionais",
        "",
        "Os requisitos do sistema definem SLA minimo de 99.9% de uptime.",
        "Cada requisito deve possuir rastreabilidade com testes automatizados.",
        "",
        "## Arquitetura de Microsservicos e Dados",
        "A arquitetura adota padrao orientado a eventos com mensageria desacoplada.",
        "O desenho arquitetural e escalavel horizontalmente.",
    ]
    while len(linhas) < total_linhas - 10:
        idx = len(linhas)
        if idx % 60 == 0:
            linhas.append(f"### Subsecao Arquitetural {idx}")
            linhas.append("Componentes comunicam-se via contratos gRPC.")
        elif idx % 40 == 0:
            linhas.append(f"### Requisitos da Camada {idx}")
            linhas.append("Requisitos de integridade referencial sao auditados.")
        else:
            linhas.append(f"Linha {idx}: detalhamento de fluxos operacionais e telemetria.")
    linhas.append("## Testes Automatizados e Validacao")
    linhas.append("A estrategia de testes cobre suites unitarias e integracao.")
    while len(linhas) < total_linhas:
        linhas.append(f"Suporte a testes na linha {len(linhas)}.")
    return "\n".join(linhas)


# =============================================================================
# CRITERIO 1: reducao de tokens <= 50% com 5 documentos grandes
# =============================================================================

def test_mapa_secoes_cinco_documentos_reducao_50_porcento(mod7):
    artefatos = {}
    for i in range(1, 6):
        nome = f"doc_fase6_{i}.md"
        conteudo = _gerar_documento_extenso(f"Modulo_{i}", total_linhas=520)
        assert len(conteudo.splitlines()) >= 500
        artefatos[nome] = conteudo

    dump_bruto = "\n\n".join(artefatos.values())
    tokens_bruto = _contar_tokens(dump_bruto)
    assert tokens_bruto > 3000

    mapa = mod7.montar_mapa_secoes(artefatos)
    tokens_mapa = _contar_tokens(mapa)

    assert tokens_mapa <= tokens_bruto * 0.5, (
        f"Mapa ({tokens_mapa} tokens) excede 50% do bruto ({tokens_bruto} tokens)"
    )


def test_mapa_secoes_preserva_topicos_chave(mod7):
    artefatos = {}
    for i in range(1, 6):
        nome = f"doc_{i}.md"
        artefatos[nome] = _gerar_documento_extenso(f"Mod_{i}", total_linhas=520)

    mapa = mod7.montar_mapa_secoes(artefatos)
    mapa_lower = mapa.lower()

    assert "requisitos" in mapa_lower
    assert "arquitetura" in mapa_lower
    assert "testes" in mapa_lower


def test_mapa_secoes_listaTodosDocumentos(mod7):
    artefatos = {f"doc_{i}.md": _gerar_documento_extenso(f"M{i}") for i in range(1, 6)}
    mapa = mod7.montar_mapa_secoes(artefatos)
    for i in range(1, 6):
        assert f"doc_{i}.md" in mapa


def test_mapa_secoes_vazio(mod7):
    assert mod7.montar_mapa_secoes({}) == ""
    assert mod7.montar_mapa_secoes(None) == ""


# =============================================================================
# FUNCOES AUXILIARES
# =============================================================================

def test_detectar_topicos_chave(mod7):
    texto = "Arquitetura limpa com requisitos funcionais e testes automatizados."
    topicos = mod7._detectar_topicos_chave(texto)
    assert "requisitos" in topicos
    assert "arquitetura" in topicos
    assert "testes" in topicos


def test_extrair_resumo_executivo(mod7):
    texto = "# Titulo\n\nPrimeira frase descritiva completa. Segunda frase detalhando. Terceira frase sobre testes. Quarta frase extra."
    resumo = mod7._extrair_resumo_executivo(texto, max_frases=3)
    assert "Primeira frase" in resumo
    assert "Quarta frase" not in resumo
    assert "# Titulo" not in resumo


# =============================================================================
# INTEGRACAO: AnalisadorCriticoAutomatico com mapa de secoes
# =============================================================================

def test_integracao_analisador_com_mapa_secoes(mod7, tmp_path):
    pasta_proj = tmp_path / "projeto_teste"
    pasta_proj.mkdir()
    cache_dir = pasta_proj / ".aidd" / "cache"
    cache_dir.mkdir(parents=True)

    docs = {
        "requisitos.md": "# Requisitos\n\nLinha com requisitos e testes.\n" + "Linha extra.\n" * 100,
        "manual.html": "<h1>Manual</h1><p>Arquitetura baseada em microsservicos. Testes rigorosos.</p>" + "<p>Texto</p>\n" * 100,
    }

    analisador = mod7.AnalisadorCriticoAutomatico(pasta_proj)
    resultado = analisador.executar(artefatos=docs)

    assert resultado["status"] == "COMPLETO"
    assert "mapa_secoes" in resultado
    assert len(resultado["mapa_secoes"]) > 0
    assert "requisitos.md" in resultado["mapa_secoes"]
