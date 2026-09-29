# -*- coding: utf-8 -*-
"""
Teste do fallback/resiliencia de aidd-enterprise (Ticket 5 / D11).
Exige:
- Erro abrupto de IO/permissao durante a injecao NAO derruba o processo:
  retry com backoff exponencial para falhas transientes.
- Falha fatal capturada em relatorio diagnostico estruturado, gravado de forma
  atomica, sem corromper o workspace.
- exit 1 (sem traceback) quando as tentativas sao esgotadas.
"""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
FALLBACK_PATH = ROOT_DIR / ".agents" / "skills" / "aidd-enterprise" / "scripts" / "fallback.py"
RELATORIO = "ENTERPRISE-DIAGNOSTICO.json"


def carregar_fallback():
    spec = importlib.util.spec_from_file_location("aidd_enterprise_fallback", str(FALLBACK_PATH))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_import_fallback():
    mod = carregar_fallback()
    assert hasattr(mod, "eh_transiente")
    assert hasattr(mod, "backoff_exponencial")
    assert hasattr(mod, "com_retry")
    assert hasattr(mod, "executar_com_fallback")
    assert hasattr(mod, "gerar_relatorio_diagnostico")
    assert hasattr(mod, "persistir_diagnostico")
    assert hasattr(mod, "ResilienciaEsgotadaError")


def test_retry_recupera_de_erro_de_permissao():
    """Lock de permissao durante a injecao e retentado ate o sucesso."""
    mod = carregar_fallback()
    chamadas = {"n": 0}
    esperas = []

    def operacao():
        chamadas["n"] += 1
        if chamadas["n"] < 3:
            raise PermissionError("permission lock durante injecao")
        return "ok"

    resultado = mod.com_retry(operacao, tentativas=3, backoff_base=0.1, esperar=esperas.append)
    assert resultado == "ok"
    assert chamadas["n"] == 3
    assert esperas == [0.1, 0.2]


def test_backoff_exponencial_e_deterministico():
    mod = carregar_fallback()
    assert mod.backoff_exponencial(1, 0.1, 2.0) == pytest.approx(0.1)
    assert mod.backoff_exponencial(2, 0.1, 2.0) == pytest.approx(0.2)
    assert mod.backoff_exponencial(3, 0.1, 2.0) == pytest.approx(0.4)
    with pytest.raises(ValueError):
        mod.backoff_exponencial(0, 0.1, 2.0)


def test_erro_nao_transiente_propaga_sem_retry():
    """Erro nao transiente propaga imediatamente (sem retry cego)."""
    mod = carregar_fallback()
    chamadas = {"n": 0}

    def operacao():
        chamadas["n"] += 1
        raise ValueError("falha logica, nao transiente")

    with pytest.raises(ValueError):
        mod.com_retry(operacao, tentativas=3, esperar=lambda s: None)
    assert chamadas["n"] == 1


def test_erros_de_disco_sao_transientes():
    mod = carregar_fallback()
    assert mod.eh_transiente(PermissionError("lock"))
    assert mod.eh_transiente(OSError(13, "Permission denied"))
    assert not mod.eh_transiente(ValueError("payload invalido"))
    assert not mod.eh_transiente(KeyError("campo"))


def test_esgotar_tentativas_lanca_e_grava_diagnostico(tmp_path):
    """Tentativas esgotadas -> ResilienciaEsgotadaError + relatorio estruturado."""
    mod = carregar_fallback()

    def operacao():
        raise PermissionError("disk io error permanente")

    with pytest.raises(mod.ResilienciaEsgotadaError):
        mod.com_retry(operacao, tentativas=3, backoff_base=0.0, esperar=lambda s: None)

    try:
        mod.com_retry(operacao, tentativas=2, backoff_base=0.0, esperar=lambda s: None)
    except mod.ResilienciaEsgotadaError as exc:
        registro = mod.gerar_relatorio_diagnostico(exc, tentativas=2, contexto={"estagio": "injecao"})
        caminho = mod.persistir_diagnostico(tmp_path, registro)

    assert caminho == tmp_path / RELATORIO
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    assert dados["tipo"] == "ResilienciaEsgotadaError"
    assert dados["tentativas"] == 2
    assert dados["contexto"]["estagio"] == "injecao"
    assert "transiente" in dados


def test_executar_com_fallback_sucesso_sem_relatorio(tmp_path):
    mod = carregar_fallback()
    assert mod.executar_com_fallback(lambda: "ok", tmp_path, tentativas=2, esperar=lambda s: None) == 0
    assert not (tmp_path / RELATORIO).exists()


def test_executar_com_fallback_falha_fatal_retorna_1_e_nao_corrompe(tmp_path):
    """Falha fatal: exit 1, relatorio diagnostico gravado, workspace intacto."""
    mod = carregar_fallback()

    def operacao():
        (tmp_path / "parcial.tmp").write_text("lixo parcial", encoding="utf-8")
        raise PermissionError("permission lock na injecao")

    codigo = mod.executar_com_fallback(
        operacao, tmp_path, tentativas=2, backoff_base=0.0, esperar=lambda s: None,
        contexto={"estagio": "injecao"},
    )
    assert codigo == 1
    relatorio = tmp_path / RELATORIO
    assert relatorio.is_file(), "relatorio diagnostico deve ser gravado"
    dados = json.loads(relatorio.read_text(encoding="utf-8"))
    assert dados["transiente"] is True
    assert dados["tentativas"] == 2
    # relatorio e JSON valido (atomico); nenhum .tmp de relatorio fica para tras
    assert not list(tmp_path.glob(f"{RELATORIO}*.tmp"))


def test_executar_com_fallback_erro_logico_retorna_1_sem_retry(tmp_path):
    mod = carregar_fallback()
    chamadas = {"n": 0}

    def operacao():
        chamadas["n"] += 1
        raise ValueError("payload invalido")

    codigo = mod.executar_com_fallback(operacao, tmp_path, tentativas=5, esperar=lambda s: None)
    assert codigo == 1
    assert chamadas["n"] == 1
    dados = json.loads((tmp_path / RELATORIO).read_text(encoding="utf-8"))
    assert dados["transiente"] is False


def test_relatorio_diagnostico_e_atomico(tmp_path):
    """Gravacao atomica: conteudo valido mesmo com escrita anterior interrompida."""
    mod = carregar_fallback()
    (tmp_path / f"{RELATORIO}.tmp").write_text("interrupcao previa", encoding="utf-8")
    registro = mod.gerar_relatorio_diagnostico(RuntimeError("boom"), tentativas=1, contexto={})
    caminho = mod.persistir_diagnostico(tmp_path, registro)
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    assert dados["tipo"] == "RuntimeError"
    assert not (tmp_path / f"{RELATORIO}.tmp").exists()


def test_subprocesso_exit_1_sem_traceback(tmp_path):
    """End-to-end: injecao com lock de permissao termina com exit 1 e sem traceback."""
    script = tmp_path / "injecao_falha.py"
    script.write_text(
        (
            "import importlib.util, sys\n"
            f"spec = importlib.util.spec_from_file_location('fb', r'{FALLBACK_PATH}')\n"
            "mod = importlib.util.module_from_spec(spec)\n"
            "spec.loader.exec_module(mod)\n"
            "def operacao():\n"
            "    raise PermissionError('permission lock')\n"
            f"sys.exit(mod.executar_com_fallback(operacao, r'{tmp_path}', tentativas=2, "
            "backoff_base=0.0, esperar=lambda s: None, contexto={'estagio': 'injecao'}))\n"
        ),
        encoding="utf-8",
    )
    res = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, timeout=60)
    assert res.returncode == 1, f"esperava exit 1 (obtido {res.returncode})"
    assert "Traceback" not in res.stderr, f"falha deve ser capturada sem traceback: {res.stderr[-500:]}"
    assert (tmp_path / RELATORIO).is_file()
