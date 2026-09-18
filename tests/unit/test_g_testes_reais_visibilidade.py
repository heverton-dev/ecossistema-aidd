# -*- coding: utf-8 -*-
"""
G_TESTES_REAIS e o unico gate do pre-commit que roda por minutos (pytest
sequencial de 7 ferramentas) -- o pre-commit so exibe a saida de um hook
depois que ele termina inteiro, entao esse gate ficava mudo/parecia travado
o tempo todo, mesmo com --verbose (achado real: usuario reportou "trava
aqui e nao consigo ver o que esta acontecendo" durante um `git commit` de
verdade, com screenshot do terminal parado em "G_TESTES_REAIS ...").

Fix: o gate agora tambem escreve progresso direto no dispositivo de
terminal de controle (CON/tty), contornando a captura de stdout do
pre-commit. Estes testes cobrem essa via alternativa isoladamente, sem
precisar rodar pytest de verdade (caro) nem um terminal de verdade.
"""

import io
import os
import sys

import pytest

GATES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "gates"))
if GATES_DIR not in sys.path:
    sys.path.insert(0, GATES_DIR)

import G_TESTES_REAIS as gate  # noqa: E402


def test_anunciar_ao_vivo_escreve_na_stream_configurada(monkeypatch):
    buffer = io.StringIO()
    monkeypatch.setattr(gate, "_CONSOLE_AO_VIVO", buffer)

    gate._anunciar_ao_vivo("[G_TESTES_REAIS] (1/7) aidd-forge: pytest rodando...")

    assert "aidd-forge" in buffer.getvalue()
    assert "pytest rodando" in buffer.getvalue()


def test_anunciar_ao_vivo_nao_quebra_sem_terminal_disponivel(monkeypatch):
    """Ambiente headless (CI, sandbox) sem terminal de controle: None, sem crash."""
    monkeypatch.setattr(gate, "_CONSOLE_AO_VIVO", None)
    gate._anunciar_ao_vivo("mensagem qualquer")  # nao deve levantar excecao


def test_anunciar_ao_vivo_nao_quebra_se_stream_falhar_ao_escrever(monkeypatch):
    """Broken pipe / dispositivo fechado no meio do commit: nunca pode derrubar o gate."""

    class StreamQuebrada:
        def write(self, *_args, **_kwargs):
            raise OSError("terminal fechado")

        def flush(self):
            raise OSError("terminal fechado")

    monkeypatch.setattr(gate, "_CONSOLE_AO_VIVO", StreamQuebrada())
    gate._anunciar_ao_vivo("mensagem qualquer")  # nao deve levantar excecao


def test_abrir_console_ao_vivo_retorna_none_quando_dispositivo_indisponivel(monkeypatch):
    """CI/sandbox sem terminal real: open() do dispositivo de console falha
    com OSError -- o gate precisa continuar funcionando (so perde o
    espelhamento ao vivo, print() normal segue intacto)."""

    def open_que_falha(*_args, **_kwargs):
        raise OSError("no such device")

    monkeypatch.setattr("builtins.open", open_que_falha)
    assert gate._abrir_console_ao_vivo() is None


def test_executar_anuncia_inicio_progresso_e_conclusao_ao_vivo(monkeypatch, tmp_path):
    """Reproducao de ponta a ponta (sem rodar pytest de verdade): FERRAMENTAS
    aponta pra diretorios inexistentes, entao cada uma cai no ramo AUSENTE,
    rapido -- mas o anuncio de inicio/fim ao vivo tem que acontecer do
    mesmo jeito, e sem duplicar por ferramenta ausente (essa nao chama
    pytest)."""
    buffer = io.StringIO()
    monkeypatch.setattr(gate, "_CONSOLE_AO_VIVO", buffer)
    monkeypatch.setattr(gate, "FERRAMENTAS", ["ferramenta-inexistente-1", "ferramenta-inexistente-2"])
    monkeypatch.setattr(gate, "TOOLS_DIR", str(tmp_path))
    monkeypatch.setattr(gate, "_carregar_allowlist", lambda: {})

    gate.executar()

    saida = buffer.getvalue()
    assert "Iniciando: 2 ferramenta(s)" in saida
    assert "Concluido:" in saida
