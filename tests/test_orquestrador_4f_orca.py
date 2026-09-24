# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — TESTE DO ORQUESTRADOR 4F: AGENTE VISÍVEL NO TERMINAL DO ORCA
=============================================================================
Problema (2026-09-24): o agente rodava oculto (Popen + claude -p), sem
visibilidade; o fim era adivinhado por um watchdog de tamanho de arquivo; e
terminal aberto na worktree travava a remoção.

Regras:
  - Modo padrão abre o agente num terminal visível do Orca (comando do ticket,
    sem -p/--print); a tarefa vai por 'dispatch --return-preamble', com o
    preâmbulo num arquivo DENTRO da worktree (git-ignorado, apagado antes do
    gate) e 1 linha no terminal pedindo p/ lê-lo; o prompt vai embutido na spec.
  - O fim vem do worker_done do próprio agente ('check --wait', sem polling).
  - Orca indisponível -> cai no modo oculto (HUD), sem quebrar o pipeline.
  - Terminais da worktree são fechados antes de devolver (evita a trava).
=============================================================================
"""

import json
import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))

import orquestrador_4f  # noqa: E402


@pytest.fixture(autouse=True)
def run_limpo(monkeypatch):
    monkeypatch.setattr(orquestrador_4f, "_run_orca", {})
    monkeypatch.setattr(orquestrador_4f.time, "sleep", lambda s: None)


def _orca_falso(chamadas, mensagens):
    def orca(*args, **kwargs):
        chamadas.append(args)
        acao = args[:2]
        if acao == ("orchestration", "run-create"):
            return {"run": {"id": "run_1"}}
        if acao == ("terminal", "create"):
            return {"terminal": {"handle": "term_x"}}
        if acao == ("orchestration", "task-create"):
            return {"task": {"id": "task_1"}}
        if acao == ("orchestration", "dispatch"):
            return {"dispatch": {"id": "ctx_1"}, "preamble": "PREAMBULO"}
        if acao == ("orchestration", "check") and "--wait" in args:
            return mensagens.pop(0) if mensagens else None
        return {}
    return orca


def _lote(dispatch_id, outcome="succeeded", tipo="worker_done"):
    payload = json.dumps({"dispatchId": dispatch_id, "outcome": outcome})
    return {"deliveryId": f"d_{dispatch_id}", "messages": [{"type": tipo, "subject": "ok", "payload": payload}]}


def test_comando_interativo_remove_flags_headless():
    assert orquestrador_4f.comando_interativo("claude --dangerously-skip-permissions -p") == \
        "claude --dangerously-skip-permissions"
    assert orquestrador_4f.comando_interativo("agy --model x -p -") == "agy --model x"
    assert orquestrador_4f.comando_interativo("claude --dangerously-skip-permissions --chrome --model haiku") == \
        "claude --dangerously-skip-permissions --chrome --model haiku"


def test_fluxo_injeta_tarefa_espera_worker_done_e_fecha_terminais(tmp_path, monkeypatch):
    chamadas = []
    monkeypatch.setattr(orquestrador_4f, "orca", _orca_falso(chamadas, [_lote("ctx_1")]))
    prompt = tmp_path / "p.txt"
    prompt.write_text("faça", encoding="utf-8")

    outcome = orquestrador_4f.run_agente_orca("claude --x -p", tmp_path, str(prompt), tmp_path / "out" / "h.md",
                                              titulo="TICKET-01")
    assert outcome == "succeeded"
    create = next(a for a in chamadas if a[:2] == ("terminal", "create"))
    assert create[create.index("--command") + 1] == "claude --x"
    spec = next(a for a in chamadas if a[:2] == ("orchestration", "task-create"))
    texto_spec = spec[spec.index("--spec") + 1]
    assert texto_spec.startswith("faça") and "out/h.md" in texto_spec  # prompt embutido, nada fora da worktree
    dispatch = next(a for a in chamadas if a[:2] == ("orchestration", "dispatch"))
    assert "--return-preamble" in dispatch and dispatch[dispatch.index("--to") + 1] == "term_x"
    preambulo = tmp_path / orquestrador_4f.PREAMBULO
    send = next(a for a in chamadas if a[:2] == ("terminal", "send"))
    assert orquestrador_4f.PREAMBULO in send[send.index("--text") + 1] and "--enter" not in send
    assert ("terminal", "send", "--terminal", "term_x", "--enter") in chamadas
    assert not preambulo.exists()
    assert any("--ack" in a for a in chamadas)
    assert chamadas[-1][:2] == ("terminal", "close") and "--all" in chamadas[-1]


def test_worker_done_de_outro_dispatch_e_ignorado(tmp_path, monkeypatch):
    chamadas = []
    monkeypatch.setattr(orquestrador_4f, "orca", _orca_falso(chamadas, [_lote("ctx_outro"), _lote("ctx_1", "failed")]))
    assert orquestrador_4f.run_agente_orca("claude", tmp_path, None, None, titulo="T") == "failed"


def test_escalation_conta_como_falha(tmp_path, monkeypatch):
    monkeypatch.setattr(orquestrador_4f, "orca", _orca_falso([], [_lote("ctx_1", tipo="escalation")]))
    assert orquestrador_4f.run_agente_orca("claude", tmp_path, None, None, titulo="T") == "failed"


def test_orca_indisponivel_cai_no_modo_oculto(tmp_path, monkeypatch):
    monkeypatch.setenv("AIDD_AGENTE_MODO", "orca")
    monkeypatch.setattr(orquestrador_4f, "orca", lambda *a, **k: None)
    chamadas = []
    monkeypatch.setattr(orquestrador_4f, "run_hud_oculto", lambda *a, **k: chamadas.append(a) or True)

    assert orquestrador_4f.run_cmd_tty("claude -p", cwd=tmp_path, expected_handoff=tmp_path / "h.md") is True
    assert len(chamadas) == 1


def test_confirma_pergunta_de_confianca_antes_da_tarefa(monkeypatch):
    # agentWait do Orca fica velho (mimo): vale só o que a tela mostra agora.
    telas = [{"terminal": {"tail": ["> Yes, I trust this folder", "No, exit"]}},
             {"terminal": {"tail": ["Type your message..."]}}]
    enviados = []

    def orca_falso(*args, **kwargs):
        if args[:2] == ("terminal", "read"):
            return telas.pop(0)
        enviados.append(args)
        return {}

    monkeypatch.setattr(orquestrador_4f, "orca", orca_falso)
    orquestrador_4f.confirmar_confianca_pasta("term_x")
    assert [a for a in enviados if a[:2] == ("terminal", "send")] == [("terminal", "send", "--terminal", "term_x", "--enter")]


def test_aviso_de_risco_com_padrao_exit_nunca_recebe_enter(monkeypatch):
    enviados = []
    tela_risco = {"terminal": {"tail": ["● No, exit (recommended)", "○ Yes, I accept the risks and want to skip permissions"]}}
    monkeypatch.setattr(orquestrador_4f, "orca",
                        lambda *a, **k: tela_risco if a[:2] == ("terminal", "read") else enviados.append(a))
    orquestrador_4f.confirmar_confianca_pasta("term_x")
    assert enviados == []


def test_sem_pergunta_de_confianca_nao_envia_nada(monkeypatch):
    enviados = []
    monkeypatch.setattr(orquestrador_4f, "orca",
                        lambda *a, **k: {"terminal": {"tail": ["pronto"]}} if a[:2] == ("terminal", "read") else enviados.append(a))
    orquestrador_4f.confirmar_confianca_pasta("term_x")
    assert enviados == []
