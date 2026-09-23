# -*- coding: utf-8 -*-
"""
Teste de Tratamento de Exceções e Fallback Operacional (Ticket 4 / D11).
Valida:
1. Lógica de retry com backoff exponencial autônomo.
2. Captura de ganchos (hooks) de retry e telemetria.
3. Fallback graceful e interrupção controlada de pipeline com preservação de estado em disco/memória.
4. Simulação de falha crítica na leitura de manifesto com parada graceful e log de estado.
5. Simulação de timeout persistente em chamada LLM/motor com geração de relatório fallback.
6. Testes de estresse para validação de resiliência e ausência de vazamento de exceções.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
SKILL_SCRIPTS = ROOT_DIR / ".agents" / "skills" / "aidd-melhoria" / "scripts"
if str(SKILL_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SKILL_SCRIPTS))

import fallback
from fallback import (
    FallbackOperacionalError,
    ManifestReadError,
    LLMTimeoutError,
    PipelineInterruptedError,
    EstadoExecucao,
    executar_com_retry,
    ler_manifesto_com_fallback,
    executar_analise_com_fallback,
    interromper_pipeline_gracefully,
)


def test_retry_com_backoff_sucesso_apos_tentativas():
    """Garante que operação que falha inicialmente se recupera com retry backoff autônomo."""
    mock_func = MagicMock()
    mock_func.side_effect = [
        TimeoutError("Timeout transitório 1"),
        TimeoutError("Timeout transitório 2"),
        {"status": "ok", "dados": 42},
    ]

    hook_logs = []
    def on_retry(tentativa: int, erro: Exception, tempo_espera: float):
        hook_logs.append({"tentativa": tentativa, "erro": str(erro), "espera": tempo_espera})

    resultado = executar_com_retry(
        mock_func,
        max_tentativas=3,
        backoff_base=0.01,
        on_retry_hook=on_retry,
    )
    assert resultado == {"status": "ok", "dados": 42}
    assert mock_func.call_count == 3
    assert len(hook_logs) == 2
    assert hook_logs[0]["tentativa"] == 1
    assert hook_logs[1]["tentativa"] == 2


def test_falha_persistente_aciona_fallback_graceful_sem_perda_de_estado(tmp_path):
    """Garante que falha persistente gera registro formal de erro sem exceção descontrolada."""
    estado = EstadoExecucao(etapa_atual="processamento_inicial", contexto={"pedido": "Refatorar módulo"})

    mock_func = MagicMock()
    mock_func.side_effect = TimeoutError("Falha irrecuperável na LLM")

    hook_logs = []
    def on_retry(tentativa: int, erro: Exception, tempo_espera: float):
        hook_logs.append(f"Tentativa {tentativa}: {erro}")

    with pytest.raises(FallbackOperacionalError) as exc_info:
        executar_com_retry(
            mock_func,
            max_tentativas=2,
            backoff_base=0.01,
            on_retry_hook=on_retry,
        )

    assert "Falha irrecuperável" in str(exc_info.value)
    assert len(hook_logs) == 1

    # Interrupção graceful do pipeline registrando estado
    arquivo_estado = tmp_path / "estado_erro.json"
    interrupcao = interromper_pipeline_gracefully(
        estado=estado,
        motivo=str(exc_info.value),
        arquivo_log=arquivo_estado,
    )

    assert interrupcao["status"] == "FALLBACK_ACIONADO"
    assert arquivo_estado.is_file()
    dados_salvos = json.loads(arquivo_estado.read_text(encoding="utf-8"))
    assert dados_salvos["contexto"]["pedido"] == "Refatorar módulo"
    assert len(dados_salvos["historico_erros"]) >= 1


def test_simulacao_falha_leitura_manifesto_interrompe_pipeline_gracefully(tmp_path):
    """Simula arquivo de manifesto corrompido ou inexistente; interrompe gracefully e salva log."""
    caminho_inexistente = tmp_path / "manifesto_fantasma.json"
    arquivo_log = tmp_path / "log_falha_manifesto.json"
    handoff_dest = tmp_path / "handoff-melhoria.json"

    estado = EstadoExecucao(etapa_atual="leitura_manifesto")

    # Execução deve tratar a falha sem estourar crash não-tratado
    resultado, estado_final = ler_manifesto_com_fallback(
        caminho_manifesto=caminho_inexistente,
        estado=estado,
        arquivo_log=arquivo_log,
        handoff_path=handoff_dest,
        max_tentativas=2,
        backoff_base=0.01,
    )

    assert resultado is None
    assert estado_final.status == "INTERROMPIDO"
    assert len(estado_final.historico_erros) >= 1
    assert arquivo_log.is_file()

    # Valida integridade do handoff gerado na interrupção
    assert handoff_dest.is_file()
    handoff_dados = json.loads(handoff_dest.read_text(encoding="utf-8"))
    assert handoff_dados["status"] == "FALHA"
    assert handoff_dados["codigo_saida"] == 1
    assert "Manifesto não encontrado" in handoff_dados["erro"]


def test_simulacao_timeout_llm_aciona_fallback_com_estado_preservado(tmp_path):
    """Simula timeout persistente na chamada à LLM/motor analítico; gera relatório determinístico de fallback."""
    arquivo_log = tmp_path / "log_timeout_llm.json"
    handoff_dest = tmp_path / "handoff-timeout.json"
    estado = EstadoExecucao(
        etapa_atual="invocacao_llm",
        contexto={"pedido": "Otimizar parsing de AST", "nome": "otimizar-ast"},
    )

    def simular_llm_travada():
        raise TimeoutError("LLM Gateway Timeout 504")

    tentativas_hook = []
    def hook_telemetria(tentativa, erro, espera):
        tentativas_hook.append((tentativa, str(erro)))

    relatorio_fallback = executar_analise_com_fallback(
        motor_ou_funcao=simular_llm_travada,
        pedido="Otimizar parsing de AST",
        nome="otimizar-ast",
        estado=estado,
        arquivo_log=arquivo_log,
        handoff_path=handoff_dest,
        max_tentativas=3,
        backoff_base=0.01,
        on_retry_hook=hook_telemetria,
    )

    # Verifica que o fallback produziu um relatório em conformidade estrita com schema
    assert "relatorio" in relatorio_fallback
    conteudo = relatorio_fallback["relatorio"]
    assert conteudo["pedido"] == "Otimizar parsing de AST"
    assert conteudo["nome"] == "otimizar-ast"
    assert "Fallback Operacional" in conteudo["resumo"]
    assert conteudo["status_operacional"] == "FALLBACK"
    assert len(tentativas_hook) == 2  # 2 retries após primeira falha em 3 tentativas

    # Verifica que o estado foi salvo e o handoff foi emitido
    assert arquivo_log.is_file()
    estado_salvo = json.loads(arquivo_log.read_text(encoding="utf-8"))
    assert estado_salvo["status"] == "FALLBACK_ACIONADO"
    assert estado_salvo["contexto"]["pedido"] == "Otimizar parsing de AST"

    assert handoff_dest.is_file()
    handoff = json.loads(handoff_dest.read_text(encoding="utf-8"))
    assert handoff["status"] == "SUCESSO_FALLBACK"
    assert handoff["codigo_saida"] == 0


def test_stress_multiplas_falhas_transitorias_e_recuperacao_hooks():
    """Teste de estresse executando 50 ciclos com falhas transitórias intermitentes e verificação de hooks."""
    total_ciclos = 50
    hook_invocacoes = 0

    def contar_hook(tentativa, erro, espera):
        nonlocal hook_invocacoes
        hook_invocacoes += 1

    for ciclo in range(total_ciclos):
        tentativa_local = 0
        def operacao_flaky():
            nonlocal tentativa_local
            tentativa_local += 1
            if tentativa_local < 2:
                raise ConnectionResetError("Falha transitória na conexão de socket")
            return f"sucesso_ciclo_{ciclo}"

        res = executar_com_retry(
            operacao_flaky,
            max_tentativas=3,
            backoff_base=0.001,
            on_retry_hook=contar_hook,
        )
        assert res == f"sucesso_ciclo_{ciclo}"

    # Cada ciclo falhou exatamente 1 vez antes do sucesso = 50 retries invocados
    assert hook_invocacoes == total_ciclos


def test_stress_interrupcoes_concorrentes_mantem_integridade_estado(tmp_path):
    """Teste de estresse simulando múltiplas falhas de pipeline consecutivas sem corrupção de arquivos."""
    for i in range(20):
        arquivo_log = tmp_path / f"estado_stress_{i}.json"
        estado = EstadoExecucao(
            etapa_atual=f"estresse_passo_{i}",
            contexto={"indice": i, "timestamp": time.time()},
        )
        estado.registrar_erro(f"passo_{i}", ValueError(f"Erro simulado #{i}"))
        
        saida = interromper_pipeline_gracefully(
            estado=estado,
            motivo=f"Interrupção forçada no estresse #{i}",
            arquivo_log=arquivo_log,
        )
        assert saida["status"] == "FALLBACK_ACIONADO"
        assert arquivo_log.is_file()

        dados = json.loads(arquivo_log.read_text(encoding="utf-8"))
        assert dados["contexto"]["indice"] == i
        assert len(dados["historico_erros"]) == 2  # 1 registrado + 1 motivo da interrupção
