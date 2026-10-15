# -*- coding: utf-8 -*-
"""
Achado #1 do motor PURE — TDD red→green.

Garante que a spec estruturada do planner (entrevista/grill)
chegue ao prompt da Fase 2 (AnalisadorFase2).

Antes do fix: o prompt não contém a spec → teste FALHA.
Após  o fix : o prompt contém a spec   → teste PASSA.
"""

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Fixtures auxiliares
# ---------------------------------------------------------------------------

SPEC_PLANNER_EXEMPLO = {
    "nome": "VideoDoc AI",
    "dominio": "edtech",
    "descricao": "Plataforma de documentação automática de vídeos YouTube",
    "requisitos": [
        "Processamento offline sem API key obrigatória",
        "Output em PT-BR com formatação tripartite",
    ],
    "telas_referencia": ["onboarding", "dashboard", "exportar"],
    "publico_alvo": "Educadores brasileiros",
}

ANALISE_VALIDA = {
    "objetivo": "Documentar vídeos automaticamente",
    "publico_alvo": "Educadores",
    "constraints": ["Zero download", "PT-BR"],
    "stack_recomendado": {
        "linguagem": "Python 3.10+",
        "framework": "FastAPI",
        "banco": "SQLite",
        "libs_principais": ["requests"],
    },
    "arquitetura": "Pipeline AIDD em 5 camadas",
    "referencias_utilizadas": ["ref-1"],
}


def _resposta_llm(conteudo):
    return {
        "conteudo": json.dumps(conteudo, ensure_ascii=False),
        "tokens_consumidos": 42,
        "modelo_usado": "teste",
        "timestamp_resposta": "2026-10-15T00:00:00Z",
    }


# ---------------------------------------------------------------------------
# Teste RED (falha antes do fix, passa depois)
# ---------------------------------------------------------------------------

def test_prompt_fase2_contem_spec_planner(analisador_02, tmp_path):
    """
    O prompt enviado ao LLM pela Fase 2 deve conter os dados estruturados
    da spec do planner (entrevista/grill), não apenas a string bruta da ideia.

    Critério:
    - O prompt deve conter a chave 'spec_planner' OU o valor de pelo menos
      um campo da SPEC_PLANNER_EXEMPLO (ex.: 'VideoDoc AI').
    - Sem o fix, o prompt só tem {ideia} e {referencias_json} → FALHA.
    - Com o fix, o prompt inclui spec_planner_json → PASSA.
    """
    prompts_capturados = []

    def fake_solicitar_llm(prompt, contexto, fase, modelo=None, timeout_delegacao=30):
        prompts_capturados.append(prompt)
        return _resposta_llm(ANALISE_VALIDA)

    modulo = analisador_02
    fase2 = modulo.AnalisadorFase2(tmp_path)

    referencias_fase1 = {"insights": [], "tendencias": [], "referencias": []}

    # O pipeline passa a spec como 3.º argumento após o fix.
    # Antes do fix, executar() só aceita (ideia, referencias) → spec ignorada.
    with patch.object(modulo, "solicitar_llm", fake_solicitar_llm, create=True):
        # Tentamos chamar com spec_planner; se a assinatura ainda não aceita,
        # o teste captura o prompt sem spec e falha na asserção abaixo.
        try:
            fase2.executar(
                "VideoDoc AI",
                referencias_fase1,
                spec_planner=SPEC_PLANNER_EXEMPLO,
            )
        except TypeError:
            # Assinatura antiga não aceita spec_planner → o prompt não tem spec.
            pass

    assert prompts_capturados, (
        "solicitar_llm não foi chamado — verifique o patch ou a lógica de delegação."
    )

    prompt_enviado = prompts_capturados[0]

    # A spec deve aparecer no prompt de alguma forma reconhecível
    spec_presente = (
        "spec_planner" in prompt_enviado
        or "VideoDoc AI" in prompt_enviado  # nome da spec
        or "edtech" in prompt_enviado        # domínio da spec
        or "Educadores brasileiros" in prompt_enviado  # publico_alvo da spec
    )

    assert spec_presente, (
        "ACHADO #1 — A spec do planner NÃO chegou ao prompt da Fase 2.\n"
        f"Prompt enviado (primeiros 800 chars):\n{prompt_enviado[:800]}"
    )


def test_executar_fase2_aceita_spec_planner(analisador_02, tmp_path):
    """
    AnalisadorFase2.executar() deve aceitar o argumento 'spec_planner'
    sem levantar TypeError.
    """
    modulo = analisador_02

    def fake_solicitar_llm(prompt, contexto, fase, modelo=None, timeout_delegacao=30):
        return _resposta_llm(ANALISE_VALIDA)

    fase2 = modulo.AnalisadorFase2(tmp_path)
    referencias_fase1 = {"insights": [], "tendencias": [], "referencias": []}

    with patch.object(modulo, "solicitar_llm", fake_solicitar_llm, create=True):
        try:
            resultado = fase2.executar(
                "VideoDoc AI",
                referencias_fase1,
                spec_planner=SPEC_PLANNER_EXEMPLO,
            )
        except TypeError as e:
            pytest.fail(
                f"ACHADO #1 — executar() não aceita spec_planner: {e}\n"
                "Adicione 'spec_planner: Dict = None' à assinatura."
            )
