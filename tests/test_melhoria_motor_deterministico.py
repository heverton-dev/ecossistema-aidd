# -*- coding: utf-8 -*-
"""
Teste de Processamento Analítico Determinístico (Ticket 3 / D8 / DoD 4).
Exige que respostas malformadas, texto puro sem JSON estruturado ou violações de schema
sejam terminantemente rejeitadas pelo validador do motor analítico (exit 1 / ValidationError).
"""

import pytest
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
SKILL_SCRIPTS = ROOT_DIR / ".agents" / "skills" / "aidd-melhoria" / "scripts"
if str(SKILL_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SKILL_SCRIPTS))


def test_validador_rejeita_texto_puro_sem_json():
    """Garante que resposta em texto puro (não estruturada) resulte em rejeição estrita."""
    from analisador import validar_resposta_analitica, AnaliseEstruturalError

    texto_puro = "Aqui esta uma analise informal sem formatacao json..."
    with pytest.raises(AnaliseEstruturalError):
        validar_resposta_analitica(texto_puro)


def test_validador_rejeita_json_sem_envelope_relatorio():
    """Garante que JSON que não segue o schema obrigatório com envelope 'relatorio' seja rejeitado."""
    from analisador import validar_resposta_analitica, AnaliseEstruturalError

    json_sem_envelope = '{"status": "ok", "mensagem": "analisado"}'
    with pytest.raises(AnaliseEstruturalError):
        validar_resposta_analitica(json_sem_envelope)


def test_validador_aceita_json_conforme():
    """Garante que JSON no schema estrito com envelope 'relatorio' seja aprovado e parseado."""
    from analisador import validar_resposta_analitica

    json_valido = '''{
        "relatorio": {
            "pedido": "Otimizar cache de memoria",
            "nota_atual": "5.0",
            "evidencia": "Cache atual consome 1GB sem expiracao",
            "recomendacao": "Sugestao de refatoracao com TTL e LRU",
            "itens_avaliados": [
                {"item": "LRU", "status": "parcial", "justificativa": "Sem expiração"}
            ]
        }
    }'''
    dados = validar_resposta_analitica(json_valido)
    assert "relatorio" in dados
    assert dados["relatorio"]["pedido"] == "Otimizar cache de memoria"


def test_cli_parser_string_malformada_crash_exit_1():
    """Garante que execução da CLI com string malformada encerra com exit 1 (crash esperado)."""
    import subprocess
    script_analisador = SKILL_SCRIPTS / "analisador.py"
    res = subprocess.run(
        [sys.executable, str(script_analisador), "{ string malformada que nao fecha"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    assert res.returncode == 1


def test_cli_parser_texto_puro_crash_exit_1():
    """Garante que execução da CLI com texto puro encerra com exit 1."""
    import subprocess
    script_analisador = SKILL_SCRIPTS / "analisador.py"
    res = subprocess.run(
        [sys.executable, str(script_analisador), "Texto puro sem json"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    assert res.returncode == 1


def test_cli_parser_json_valido_sucesso_exit_0():
    """Garante que execução da CLI com JSON estruturado conforme encerra com exit 0."""
    import subprocess
    script_analisador = SKILL_SCRIPTS / "analisador.py"
    json_valido = '{"relatorio": {"pedido": "Otimizar cache", "nota_atual": "5.0"}}'
    res = subprocess.run(
        [sys.executable, str(script_analisador), json_valido],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    assert res.returncode == 0
    assert "relatorio" in res.stdout


def test_motor_deterministico_gera_relatorio_conforme_schema():
    """Garante que o motor analítico determinístico substitui 100% LLM gerando JSON conforme."""
    from analisador import MotorAnaliticoDeterministico

    motor = MotorAnaliticoDeterministico()
    relatorio_dict = motor.processar_analise(
        pedido="Otimizar desempenho de leitura em disco",
        nota_atual="6.0",
        evidencia="I/O alto em disco mecânico"
    )
    assert "relatorio" in relatorio_dict
    rel = relatorio_dict["relatorio"]
    assert rel["pedido"] == "Otimizar desempenho de leitura em disco"
    assert "recomendacao" in rel
    assert "Sugestão de refatoração" in rel["recomendacao"]
