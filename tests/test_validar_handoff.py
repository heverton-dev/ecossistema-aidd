import hashlib
import json
import os
import sys
from pathlib import Path
import tempfile
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts import validar_handoff


def _make_handoff(tmpdir: Path, **overrides):
    handoff = {
        "versao_schema": "1.0.0",
        "servidor_sobe": True,
        "projetado_por": "test-tool",
        "produzido_por": "test-tool",
        "slice_path": str(tmpdir / "src" / "slice"),
        "evidencias": [
            {
                "caminho": str(tmpdir / "evid" / "file.txt"),
                "sha256": hashlib.sha256(b"").hexdigest(),  # arquivo vazio
                "http_status_medido": 200,
            }
        ],
        "log_erros": [],
    }
    handoff.update(overrides)
    return handoff


def test_servidor_sobe_true_sem_log_passa(tmp_path):
    handoff_path = tmp_path / "HANDOFF.json"
    handoff = _make_handoff(tmp_path)
    # Cria arquivos de evidência
    (tmp_path / "evid").mkdir(parents=True, exist_ok=True)
    (tmp_path / "evid" / "file.txt").write_text("", encoding="utf-8")
    (tmp_path / "src" / "slice").mkdir(parents=True, exist_ok=True)
    handoff["evidencias"][0]["sha256"] = hashlib.sha256(b"").hexdigest()
    handoff_path.write_text(json.dumps(handoff), encoding="utf-8")
    assert validar_handoff.validar_handoff(str(handoff_path)) is True


def test_falta_slice_path_falha(tmp_path):
    handoff_path = tmp_path / "HANDOFF.json"
    handoff = _make_handoff(tmp_path)
    handoff["slice_path"] = str(tmp_path / "inexistente")
    (tmp_path / "evid").mkdir(parents=True, exist_ok=True)
    (tmp_path / "evid" / "file.txt").write_text("", encoding="utf-8")
    handoff_path.write_text(json.dumps(handoff), encoding="utf-8")
    assert validar_handoff.validar_handoff(str(handoff_path)) is False


def test_produzido_por_nao_confere_falha(tmp_path):
    handoff_path = tmp_path / "HANDOFF.json"
    handoff = _make_handoff(tmp_path)
    handoff["produzido_por"] = "outra-ferramenta"
    (tmp_path / "evid").mkdir(parents=True, exist_ok=True)
    (tmp_path / "evid" / "file.txt").write_text("", encoding="utf-8")
    (tmp_path / "src" / "slice").mkdir(parents=True, exist_ok=True)
    handoff_path.write_text(json.dumps(handoff), encoding="utf-8")
    assert validar_handoff.validar_handoff(str(handoff_path)) is False


def test_dry_run_run_fluxo_nao_imprime_100_por_cento(tmp_path, capsys):
    # Simula execução dry-run de run-fluxo - não deve imprimir "100 percent approval"
    from scripts import orquestrador_sincrono
    orq = orquestrador_sincrono.OrquestradorSincrono(
        fluxo=1,
        nome="Teste",
        slug="teste",
        dominio="test",
        pasta=str(tmp_path / "projeto"),
        dry_run=True,
    )
    orq.executar_fluxo_completo()
    captured = capsys.readouterr()
    assert "100 percent approval" not in (captured.out + captured.err).lower()
