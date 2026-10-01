# -*- coding: utf-8 -*-
"""
Testes do Item 4 — otimizacao-tokenomics-latencia:
hermeticidade verificável de sessões + rotulagem de telemetria [TK-6].

Critérios de saída do plano (docs/planos/a-fazer/02-otimizacao-tokenomics-latencia/
04-hermeticidade-verificavel-sessoes-e-rotulagem-telemetria.md):
1. Flags de sessão limpa/efêmera garantidas em solicitar_llm_modo_headless.
2. Gate AST garante que nenhum executor headless dispare processo sem isolamento.
3. Telemetria de tokens rotulada: sessao_isolada vs sessao_compartilhada_delegada.
"""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent
_PHASES_DIR = _ROOT / 'scripts' / 'phases'
if str(_PHASES_DIR) not in sys.path:
    sys.path.insert(0, str(_PHASES_DIR))


@pytest.fixture(scope='module')
def ud():
    spec = importlib.util.spec_from_file_location(
        'utils_delegacao_item4', str(_PHASES_DIR / 'utils_delegacao.py')
    )
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


# =============================================================================
# CRITÉRIO 3: rotulagem de tipo de sessão na telemetria
# =============================================================================

def test_rotular_tipo_sessao_headless_e_isolada(ud):
    assert ud.rotular_tipo_sessao('headless') == ud.SESSAO_ISOLADA
    assert ud.SESSAO_ISOLADA == 'sessao_isolada'


def test_rotular_tipo_sessao_delegado_e_compartilhada(ud):
    assert ud.rotular_tipo_sessao('delegado') == ud.SESSAO_COMPARTILHADA_DELEGADA
    assert ud.SESSAO_COMPARTILHADA_DELEGADA == 'sessao_compartilhada_delegada'


def test_modo_delegado_rotula_sessao_compartilhada(ud, monkeypatch, tmp_path):
    """Fluxo delegado completo: resposta recebe tipo_sessao honesto."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(ud, 'INTERVALO_POLLING_INICIAL', 0.01)
    monkeypatch.setattr(ud, 'INTERVALO_POLLING_MAX', 0.02)

    resposta_falsa = {
        'conteudo': '{"ok": true}',
        'tokens_consumidos': 42,
        'modelo_usado': 'teste',
        'timestamp_resposta': '2026-09-09T00:00:00Z',
    }
    monkeypatch.setattr(
        ud.RequisicaoLLMDelegada, 'aguardar_resposta',
        lambda req_id, timeout=None, fase=None: resposta_falsa,
    )

    resultado = ud.solicitar_llm_modo_delegado('prompt', 'ctx', 'phase_02', timeout=1)
    assert resultado is not None
    assert resultado['origem_medicao'] == 'autodeclarado'
    assert resultado['tipo_sessao'] == 'sessao_compartilhada_delegada'


def test_modo_headless_rotula_sessao_isolada(ud, monkeypatch):
    """Fluxo headless: resposta litellm recebe tipo_sessao = sessao_isolada."""
    resposta_fake = type('R', (), {})()
    resposta_fake.choices = [type('C', (), {})()]
    resposta_fake.choices[0].message = type('M', (), {})()
    resposta_fake.choices[0].message.content = '{"ok": 1}'
    resposta_fake.usage = type('U', (), {})()
    resposta_fake.usage.total_tokens = 7

    litellm_fake = type('L', (), {})()
    litellm_fake.completion = lambda **kw: resposta_fake

    monkeypatch.setitem(sys.modules, 'litellm', litellm_fake)
    monkeypatch.setenv('LLM_MODEL', 'fake/modelo-teste')

    resultado = ud.solicitar_llm_modo_headless('prompt', 'ctx', 'phase_02', modelo='fake/modelo-teste')
    assert resultado is not None
    assert resultado['tipo_sessao'] == 'sessao_isolada'
    assert resultado['origem_medicao'] == 'medido_api'


# =============================================================================
# CRITÉRIO 1: flags de sessão efêmera em comandos headless
# =============================================================================

def test_flags_por_harness_existentes(ud):
    esperados = {'claude', 'codex', 'agy', 'opencode', 'mimo', 'gemini', 'hermes'}
    assert esperados.issubset(set(ud.FLAGS_SESSAO_EFEMERA_POR_HARNESS.keys()))


def test_validar_sessao_hermetica_detecta_ausencia(ud):
    relatorio = ud.validar_sessao_hermetica(['claude', '--print', 'prompt'])
    assert relatorio['hermetico'] is False
    assert relatorio['harness'] == 'claude'
    assert relatorio['flag_exigida'] == '--no-session-persistence'


def test_validar_sessao_hermetica_detecta_presenca(ud):
    relatorio = ud.validar_sessao_hermetica(['claude', '--no-session-persistence', '--print', 'p'])
    assert relatorio['hermetico'] is True
    assert relatorio['flags_presentes'] == ['--no-session-persistence']


def test_forcar_sessao_hermetica_injeta_flag(ud):
    comando = ud.forcar_sessao_hermetica(['codex', 'exec', 'tarefa'])
    assert '--ephemeral' in comando
    # Idempotente: não duplica
    comando2 = ud.forcar_sessao_hermetica(comando)
    assert comando2.count('--ephemeral') == 1


def test_forcar_sessao_hermetica_harness_desconhecido_nao_altera(ud):
    comando = ['ferramenta-xyz', 'rodar']
    assert ud.forcar_sessao_hermetica(comando) == comando


def test_validar_comando_vazio_seguro(ud):
    relatorio = ud.validar_sessao_hermetica([])
    assert relatorio['hermetico'] is False


# =============================================================================
# CRITÉRIO 2: gate AST aprova o repositório e reprova argv sem flag
# =============================================================================

def _carregar_gate():
    spec = importlib.util.spec_from_file_location(
        'g_sessao_hermetica', str(_ROOT / 'scripts' / 'gates' / 'G_SESSAO_HERMETICA.py')
    )
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def test_gate_aprova_repositorio_atual():
    gate = _carregar_gate()
    assert gate.main() == 0


def test_gate_detecta_invocacao_sem_flag(tmp_path):
    gate = _carregar_gate()
    codigo = (
        "import subprocess\n"
        "subprocess.run(['claude', '--print', 'prompt'], timeout=30)\n"
    )
    arquivo = tmp_path / 'executor_mau.py'
    arquivo.write_text(codigo, encoding='utf-8')
    violacoes = gate.auditar_arquivo(arquivo)
    assert len(violacoes) == 1
    assert violacoes[0][2] == 'claude'


def test_gate_aceita_invocacao_com_flag(tmp_path):
    gate = _carregar_gate()
    codigo = (
        "import subprocess\n"
        "subprocess.run(['claude', '--no-session-persistence', '--print', 'p'], timeout=30)\n"
    )
    arquivo = tmp_path / 'executor_bom.py'
    arquivo.write_text(codigo, encoding='utf-8')
    assert gate.auditar_arquivo(arquivo) == []


def test_gate_nao_afeta_comandos_nao_llm(tmp_path):
    gate = _carregar_gate()
    codigo = (
        "import subprocess\n"
        "subprocess.run(['git', 'status'], timeout=10)\n"
        "subprocess.run(['python', '-m', 'pytest', '-q'], timeout=60)\n"
    )
    arquivo = tmp_path / 'executor_neutro.py'
    arquivo.write_text(codigo, encoding='utf-8')
    assert gate.auditar_arquivo(arquivo) == []
