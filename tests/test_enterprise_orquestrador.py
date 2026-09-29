# -*- coding: utf-8 -*-
"""
Teste do orquestrador multi-estagio de aidd-enterprise (Ticket 4 / D10).
Exige:
- Pipeline estrito: prevalidacao -> snapshot -> injecao -> verificacao -> handoff.
- Prevalidacao pulada, estado corrompido ou estagio desconhecido -> exit 1.
- Falha de estagio -> aborto com exit 1 e status 'abortado' persistido no
  arquivo de sessao estruturado.
"""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
ORQ_PATH = ROOT_DIR / ".agents" / "skills" / "aidd-enterprise" / "scripts" / "orquestrador.py"
ARQUIVO_ESTADO = "ORQUESTRADOR-ESTADO.json"

ESTAGIOS_ESPERADOS = ("prevalidacao", "snapshot", "injecao", "verificacao", "handoff")


def carregar_orquestrador():
    spec = importlib.util.spec_from_file_location("aidd_enterprise_orquestrador", str(ORQ_PATH))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_import_orquestrador():
    orq = carregar_orquestrador()
    assert hasattr(orq, "ESTAGIOS")
    assert hasattr(orq, "carregar_estado")
    assert hasattr(orq, "executar_pipeline")
    assert hasattr(orq, "main")
    assert hasattr(orq, "EstadoCorrompidoError")
    assert orq.ESTAGIOS == ESTAGIOS_ESPERADOS


def test_pipeline_completo_retorna_exit_0(tmp_path):
    orq = carregar_orquestrador()
    pasta = tmp_path / "alvo"
    pasta.mkdir()
    assert orq.executar_pipeline(pasta) == 0

    estado = json.loads((pasta / ARQUIVO_ESTADO).read_text(encoding="utf-8"))
    assert estado["status"] == "concluido"
    assert estado["concluidos"] == list(ESTAGIOS_ESPERADOS)
    assert (pasta / "ORQUESTRADOR-SNAPSHOT.json").is_file()
    assert (pasta / "ORQUESTRADOR-MARCADOR.txt").is_file()
    assert (pasta / "HANDOFF-ENTERPRISE.json").is_file()


def test_prevalidacao_pulada_aborta_com_exit_1(tmp_path):
    """Estado que pula a prevalidacao (primeiro estagio) -> exit 1."""
    orq = carregar_orquestrador()
    pasta = tmp_path / "alvo"
    pasta.mkdir()
    (pasta / ARQUIVO_ESTADO).write_text(
        json.dumps({"versao": 1, "concluidos": ["snapshot"], "status": "em_execucao"}),
        encoding="utf-8",
    )
    assert orq.executar_pipeline(pasta) == 1


def test_estado_json_invalido_aborta_com_exit_1(tmp_path):
    """Estado intermediario corrompido -> exit 1."""
    orq = carregar_orquestrador()
    pasta = tmp_path / "alvo"
    pasta.mkdir()
    (pasta / ARQUIVO_ESTADO).write_text("{corrompido", encoding="utf-8")
    assert orq.executar_pipeline(pasta) == 1


def test_estado_estagio_desconhecido_aborta_com_exit_1(tmp_path):
    orq = carregar_orquestrador()
    pasta = tmp_path / "alvo"
    pasta.mkdir()
    (pasta / ARQUIVO_ESTADO).write_text(
        json.dumps({"versao": 1, "concluidos": ["estagio_fantasma"], "status": "em_execucao"}),
        encoding="utf-8",
    )
    assert orq.executar_pipeline(pasta) == 1


def test_estado_ordem_de_estagios_invalida_aborta_com_exit_1(tmp_path):
    """concluidos fora de ordem topologica -> exit 1."""
    orq = carregar_orquestrador()
    pasta = tmp_path / "alvo"
    pasta.mkdir()
    (pasta / ARQUIVO_ESTADO).write_text(
        json.dumps(
            {
                "versao": 1,
                "concluidos": ["prevalidacao", "injecao", "snapshot"],
                "status": "em_execucao",
            }
        ),
        encoding="utf-8",
    )
    assert orq.executar_pipeline(pasta) == 1


def test_falha_de_estagio_aborta_e_persiste_estado(tmp_path):
    """Falha na injecao -> exit 1, status abortado, etapas seguintes nunca executam."""
    orq = carregar_orquestrador()
    pasta = tmp_path / "alvo"
    pasta.mkdir()

    handlers = {e: (lambda: 1) if e == "injecao" else (lambda: 0) for e in ESTAGIOS_ESPERADOS}
    assert orq.executar_pipeline(pasta, handlers=handlers) == 1

    estado = json.loads((pasta / ARQUIVO_ESTADO).read_text(encoding="utf-8"))
    assert estado["status"] == "abortado"
    assert estado["concluidos"] == ["prevalidacao", "snapshot"]


def test_estagio_lanca_excecao_aborta_com_exit_1(tmp_path):
    orq = carregar_orquestrador()
    pasta = tmp_path / "alvo"
    pasta.mkdir()

    def estagio_explosivo():
        raise RuntimeError("snapshot quebrado")

    handlers = {e: (lambda: 0) for e in ESTAGIOS_ESPERADOS}
    handlers["snapshot"] = estagio_explosivo
    assert orq.executar_pipeline(pasta, handlers=handlers) == 1
    estado = json.loads((pasta / ARQUIVO_ESTADO).read_text(encoding="utf-8"))
    assert estado["status"] == "abortado"
    assert estado["concluidos"] == ["prevalidacao"]


def test_retomada_de_estado_valido_parcial(tmp_path):
    """Prefixo valido de concluidos retoma do proximo estagio (transicao valida)."""
    orq = carregar_orquestrador()
    pasta = tmp_path / "alvo"
    pasta.mkdir()
    (pasta / ARQUIVO_ESTADO).write_text(
        json.dumps({"versao": 1, "concluidos": ["prevalidacao", "snapshot"], "status": "em_execucao"}),
        encoding="utf-8",
    )
    executados = []

    def registrar(nome):
        def _h():
            executados.append(nome)
            return 0

        return _h

    handlers = {e: registrar(e) for e in ESTAGIOS_ESPERADOS}
    assert orq.executar_pipeline(pasta, handlers=handlers) == 0
    assert executados == ["injecao", "verificacao", "handoff"]


def test_handoff_exige_verificacao_concluida(tmp_path):
    """Handoff sem verificacao concluida (pulo de fase) -> exit 1."""
    orq = carregar_orquestrador()
    pasta = tmp_path / "alvo"
    pasta.mkdir()
    (pasta / ARQUIVO_ESTADO).write_text(
        json.dumps(
            {
                "versao": 1,
                "concluidos": ["prevalidacao", "snapshot", "injecao"],
                "status": "em_execucao",
            }
        ),
        encoding="utf-8",
    )
    handlers = {e: (lambda: 0) for e in ESTAGIOS_ESPERADOS}
    # verificacao reporta falha simulando etapa corrompida
    handlers["verificacao"] = lambda: 1
    assert orq.executar_pipeline(pasta, handlers=handlers) == 1
    estado = json.loads((pasta / ARQUIVO_ESTADO).read_text(encoding="utf-8"))
    assert estado["status"] == "abortado"
    assert "handoff" not in estado["concluidos"]


def test_main_sem_argumento_retorna_exit_1():
    orq = carregar_orquestrador()
    assert orq.main([]) == 1


def test_main_diretorio_inexistente_retorna_exit_1(tmp_path):
    orq = carregar_orquestrador()
    assert orq.main([str(tmp_path / "nao_existe")]) == 1


def test_subprocesso_exit_1_em_estado_corrompido(tmp_path):
    pasta = tmp_path / "alvo"
    pasta.mkdir()
    (pasta / ARQUIVO_ESTADO).write_text("nao e json", encoding="utf-8")
    res = subprocess.run(
        [sys.executable, str(ORQ_PATH), str(pasta)],
        capture_output=True,
        text=True,
        cwd=str(ROOT_DIR),
        timeout=120,
    )
    assert res.returncode == 1, f"esperava exit 1 (obtido {res.returncode})"
