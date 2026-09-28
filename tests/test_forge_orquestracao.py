# -*- coding: utf-8 -*-
"""
Teste da orquestracao multi-estagio de aidd-forge (Ticket 4 / D10 / DoD 4 parcial).
Exige:
- Pipeline sequencial com transicoes de estado: pre-validacao -> injecao ->
  pos-verificacao.
- Estado intermediario corrompido (JSON invalido, ordem errada, estagio
  desconhecido) -> aborto com exit 1.
- Falha de estagio -> aborto com exit 1 e status 'abortado' persistido.
"""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
ORQ_PATH = ROOT_DIR / ".agents" / "skills" / "aidd-forge" / "scripts" / "orquestracao.py"
ARQUIVO_ESTADO = "ORQUESTRACAO-ESTADO.json"


def carregar_orquestracao():
    spec = importlib.util.spec_from_file_location("aidd_forge_orquestracao", str(ORQ_PATH))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_import_orquestracao():
    orq = carregar_orquestracao()
    assert hasattr(orq, "ESTAGIOS")
    assert hasattr(orq, "carregar_estado")
    assert hasattr(orq, "executar_pipeline")
    assert hasattr(orq, "main")
    assert hasattr(orq, "EstadoCorrompidoError")
    assert orq.ESTAGIOS == ("pre_validacao", "injecao", "pos_verificacao")


def test_pipeline_completo_retorna_exit_0(tmp_path):
    orq = carregar_orquestracao()
    pasta = tmp_path / "alvo"
    pasta.mkdir()
    assert orq.executar_pipeline(pasta) == 0

    estado = json.loads((pasta / ARQUIVO_ESTADO).read_text(encoding="utf-8"))
    assert estado["status"] == "concluido"
    assert estado["concluidos"] == ["pre_validacao", "injecao", "pos_verificacao"]
    assert (pasta / "ORQUESTRACAO-MARCADOR.txt").is_file()


def test_estado_json_invalido_aborta_com_exit_1(tmp_path):
    """Estado intermediario corrompido -> exit 1."""
    orq = carregar_orquestracao()
    pasta = tmp_path / "alvo"
    pasta.mkdir()
    (pasta / ARQUIVO_ESTADO).write_text("{corrompido", encoding="utf-8")
    assert orq.executar_pipeline(pasta) == 1


def test_estado_ordem_de_estagios_invalida_aborta_com_exit_1(tmp_path):
    """concluidos fora de ordem topologica -> exit 1."""
    orq = carregar_orquestracao()
    pasta = tmp_path / "alvo"
    pasta.mkdir()
    (pasta / ARQUIVO_ESTADO).write_text(
        json.dumps({"versao": 1, "concluidos": ["injecao", "pre_validacao"], "status": "em_execucao"}),
        encoding="utf-8",
    )
    assert orq.executar_pipeline(pasta) == 1


def test_estado_estagio_desconhecido_aborta_com_exit_1(tmp_path):
    orq = carregar_orquestracao()
    pasta = tmp_path / "alvo"
    pasta.mkdir()
    (pasta / ARQUIVO_ESTADO).write_text(
        json.dumps({"versao": 1, "concluidos": ["estagio_fantasma"], "status": "em_execucao"}),
        encoding="utf-8",
    )
    assert orq.executar_pipeline(pasta) == 1


def test_falha_de_estagio_aborta_e_persiste_estado(tmp_path):
    """Falha na injecao -> exit 1, status abortado, pos-verificacao nunca executa."""
    orq = carregar_orquestracao()
    pasta = tmp_path / "alvo"
    pasta.mkdir()

    handlers = {
        "pre_validacao": lambda: 0,
        "injecao": lambda: 1,
        "pos_verificacao": lambda: 0,
    }
    assert orq.executar_pipeline(pasta, handlers=handlers) == 1

    estado = json.loads((pasta / ARQUIVO_ESTADO).read_text(encoding="utf-8"))
    assert estado["status"] == "abortado"
    assert estado["concluidos"] == ["pre_validacao"]


def test_estagio_lanca_excecao_aborta_com_exit_1(tmp_path):
    orq = carregar_orquestracao()
    pasta = tmp_path / "alvo"
    pasta.mkdir()

    def estagio_explosivo():
        raise RuntimeError("injecao quebrada")

    handlers = {
        "pre_validacao": lambda: 0,
        "injecao": estagio_explosivo,
        "pos_verificacao": lambda: 0,
    }
    assert orq.executar_pipeline(pasta, handlers=handlers) == 1
    estado = json.loads((pasta / ARQUIVO_ESTADO).read_text(encoding="utf-8"))
    assert estado["status"] == "abortado"


def test_retomada_de_estado_valido_parcial(tmp_path):
    """Prefixo valido de concluidos retoma do proximo estagio (transicao valida)."""
    orq = carregar_orquestracao()
    pasta = tmp_path / "alvo"
    pasta.mkdir()
    (pasta / ARQUIVO_ESTADO).write_text(
        json.dumps({"versao": 1, "concluidos": ["pre_validacao"], "status": "em_execucao"}),
        encoding="utf-8",
    )
    executados = []

    def registrar(nome):
        def _h():
            executados.append(nome)
            return 0
        return _h

    handlers = {
        "pre_validacao": registrar("pre_validacao"),
        "injecao": registrar("injecao"),
        "pos_verificacao": registrar("pos_verificacao"),
    }
    assert orq.executar_pipeline(pasta, handlers=handlers) == 0
    assert executados == ["injecao", "pos_verificacao"]


def test_main_sem_argumento_retorna_exit_1():
    orq = carregar_orquestracao()
    assert orq.main([]) == 1


def test_main_diretorio_inexistente_retorna_exit_1(tmp_path):
    orq = carregar_orquestracao()
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
