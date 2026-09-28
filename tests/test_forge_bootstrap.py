# -*- coding: utf-8 -*-
"""
Teste do bootstrap deterministico de aidd-forge (Ticket 3 / D8 / DoD 3).
Exige:
- Validacao estrita de schema do payload de bootstrap (JSON nao estruturado,
  tipos errados, chaves desconhecidas, faltantes) -> exit 1.
- Renderizacao deterministica de templates com placeholders totalmente resolvidos.
- Checagem de injecao: escrita confinada ao diretorio alvo via isolamento.
"""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
BOOTSTRAP_PATH = ROOT_DIR / ".agents" / "skills" / "aidd-forge" / "scripts" / "bootstrap.py"


def carregar_bootstrap():
    spec = importlib.util.spec_from_file_location("aidd_forge_bootstrap", str(BOOTSTRAP_PATH))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def payload_valido(**trocas):
    base = {
        "tool": "aidd-forge",
        "ciclo": "ciclo-01",
        "alvo": "alvo-projeto",
        "kits": ["governanca", "hooks"],
        "force": False,
    }
    base.update(trocas)
    return base


def test_import_bootstrap():
    boot = carregar_bootstrap()
    assert hasattr(boot, "validar_payload")
    assert hasattr(boot, "carregar_payload")
    assert hasattr(boot, "renderizar_template")
    assert hasattr(boot, "main")
    assert hasattr(boot, "PayloadValidationError")


def test_payload_valido_e_aceito():
    boot = carregar_bootstrap()
    normalizado = boot.validar_payload(payload_valido())
    assert normalizado["tool"] == "aidd-forge"
    assert normalizado["force"] is False


@pytest.mark.parametrize(
    "trocas",
    [
        {"tool": ""},
        {"tool": "AIDD Forge!"},
        {"ciclo": "qualquer-coisa"},
        {"alvo": "../fora_do_escopo"},
        {"kits": []},
        {"kits": [123]},
        {"force": "sim"},
    ],
)
def test_payload_invalido_dispara_erro(trocas):
    boot = carregar_bootstrap()
    with pytest.raises(boot.PayloadValidationError):
        boot.validar_payload(payload_valido(**trocas))


def test_chave_desconhecida_e_rejeitada():
    boot = carregar_bootstrap()
    with pytest.raises(boot.PayloadValidationError):
        boot.validar_payload(payload_valido(extra="nao-previsto"))


def test_chave_ausente_e_rejeitada():
    boot = carregar_bootstrap()
    dados = payload_valido()
    del dados["kits"]
    with pytest.raises(boot.PayloadValidationError):
        boot.validar_payload(dados)


def test_input_nao_estruturado_e_rejeitado():
    """JSON invalido / texto livre -> PayloadValidationError (exit 1 no CLI)."""
    boot = carregar_bootstrap()
    with pytest.raises(boot.PayloadValidationError):
        boot.carregar_payload("forge init por favor, sem schema nenhum")
    with pytest.raises(boot.PayloadValidationError):
        boot.carregar_payload(json.dumps({"tool": "aidd-forge"}))  # incompleto


def test_renderizacao_deterministica():
    boot = carregar_bootstrap()
    saida = boot.renderizar_template("tool={{tool}} ciclo={{ciclo}}", {"tool": "x", "ciclo": "ciclo-01"})
    assert saida == "tool=x ciclo=ciclo-01"


def test_placeholder_nao_resolvido_falha():
    boot = carregar_bootstrap()
    with pytest.raises(boot.PayloadValidationError):
        boot.renderizar_template("ola {{inexistente}}", {"tool": "x"})


def test_main_com_payload_invalido_retorna_exit_1(tmp_path):
    boot = carregar_bootstrap()
    arquivo = tmp_path / "payload.json"
    arquivo.write_text(json.dumps({"tool": "aidd-forge"}), encoding="utf-8")
    assert boot.main([str(arquivo)]) == 1


def test_main_com_input_nao_estruturado_retorna_exit_1(tmp_path):
    boot = carregar_bootstrap()
    arquivo = tmp_path / "payload.txt"
    arquivo.write_text("apenas texto livre", encoding="utf-8")
    assert boot.main([str(arquivo)]) == 1


def test_main_com_payload_valido_retorna_exit_0_e_confinado(tmp_path):
    boot = carregar_bootstrap()
    destino = tmp_path / "projeto_alvo"
    destino.mkdir()
    arquivo = tmp_path / "payload.json"
    arquivo.write_text(
        json.dumps(payload_valido(alvo=str(destino))),
        encoding="utf-8",
    )
    assert boot.main([str(arquivo)]) == 0
    manifesto = destino / "FORGE-BOOTSTRAP.json"
    assert manifesto.is_file()
    dados = json.loads(manifesto.read_text(encoding="utf-8"))
    assert dados["tool"] == "aidd-forge"
    assert dados["ciclo"] == "ciclo-01"


def test_main_sem_argumento_retorna_exit_1():
    """Parametro faltante -> exit 1."""
    boot = carregar_bootstrap()
    assert boot.main([]) == 1


def test_injecao_fora_do_alvo_retorna_exit_1(tmp_path):
    """Checagem de injecao: alvo com traversal nao escreve fora do diretorio."""
    boot = carregar_bootstrap()
    destino = tmp_path / "projeto_alvo"
    destino.mkdir()
    arquivo = tmp_path / "payload.json"
    arquivo.write_text(json.dumps(payload_valido(alvo="../fuga")), encoding="utf-8")
    assert boot.main([str(arquivo)]) == 1
    assert not (tmp_path / "fuga" / "FORGE-BOOTSTRAP.json").exists()


def test_subprocesso_exit_1_para_payload_invalido(tmp_path):
    """End-to-end: subprocesso do CLI termina com exit 1 em payload invalido."""
    arquivo = tmp_path / "payload.json"
    arquivo.write_text("{not json", encoding="utf-8")
    res = subprocess.run(
        [sys.executable, str(BOOTSTRAP_PATH), str(arquivo)],
        capture_output=True,
        text=True,
        cwd=str(ROOT_DIR),
        timeout=120,
    )
    assert res.returncode == 1, f"esperava exit 1 (obtido {res.returncode}): {res.stderr[-500:]}"
