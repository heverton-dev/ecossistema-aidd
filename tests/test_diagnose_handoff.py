# -*- coding: utf-8 -*-
"""
Teste de Output Consolidado e Handoff Estruturado do aidd-diagnose (Ticket 8 / D15 / DoD 8).

Red: diagnóstico completo sem `handoff-diagnose.json` deve BLOQUEAR a transição
para a próxima ferramenta (aidd-tdd ou aidd-handoff) — exit 1.
Green: handoff emitido em docs/diagnosticos/<data>_<slug>/handoff-diagnose.json,
assinado (sha256 canônico ou HMAC), com causa-raiz, arquivos alterados, teste de
regressão, status do G_aidd_diagnose e próxima ferramenta — consumível (exit 0).
"""

from __future__ import annotations

import datetime
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
DIAG_SCRIPTS = ROOT_DIR / ".agents" / "skills" / "aidd-diagnose" / "scripts"
HANDOFF_PY = DIAG_SCRIPTS / "handoff.py"

# Carregado sob nome de módulo próprio ('handoff' pertence a
# aidd-melhoria/scripts e aidd-diagnose/scripts: nomes únicos evitam
# que um teste sequestre o import do outro na mesma sessão de pytest).
_DIAG_HANDOFF_MOD = "aidd_diagnose_handoff_test"
handoff = None
_spec = importlib.util.spec_from_file_location(_DIAG_HANDOFF_MOD, HANDOFF_PY)
if _spec is not None and _spec.loader is not None:
    _modulo_handoff = importlib.util.module_from_spec(_spec)
    sys.modules[_DIAG_HANDOFF_MOD] = _modulo_handoff
    try:
        _spec.loader.exec_module(_modulo_handoff)
        handoff = _modulo_handoff  # noqa - carregado dinamicamente (estado RED tolerante)
    except Exception:
        handoff = None


CAUSA_RAIZ = "A função calcular_impacto recebia None quando a flag de inicialização não era setada."
TESTE_REGRESSAO_CONTEUDO = "def test_calcular_impacto_real():\n    assert calcular_impacto(1, 2) == 3\n"


def _rodar_cli(*argumentos: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(HANDOFF_PY), *argumentos],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )


def _criar_sessao(tmp_path: Path) -> Path:
    """Cria uma sessão completa (Ticket 1) sob tmp_path/docs/diagnosticos/."""
    hoje = datetime.date.today().strftime("%Y%m%d")
    sessao_dir = tmp_path / "docs" / "diagnosticos" / f"{hoje}_regressao-impacto"
    sessao_dir.mkdir(parents=True, exist_ok=True)
    (sessao_dir / "sessao.json").write_text(
        json.dumps(
            {
                "sintoma": "Regressao no calculo de impacto",
                "data_inicio": "2026-09-24T10:00:00",
                "fase_atual": 5,
                "fases_completadas": [1, 2, 3, 4, 5],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return sessao_dir


def _arquivos_pipeline(tmp_path: Path):
    arquivo_alterado = tmp_path / "src" / "modulo_impacto.py"
    arquivo_alterado.parent.mkdir(parents=True, exist_ok=True)
    arquivo_alterado.write_text(
        "def calcular_impacto(a, b):\n    return a + b\n", encoding="utf-8"
    )
    teste_regressao = tmp_path / "tests" / "test_modulo_impacto.py"
    teste_regressao.parent.mkdir(parents=True, exist_ok=True)
    teste_regressao.write_text(TESTE_REGRESSAO_CONTEUDO, encoding="utf-8")
    return arquivo_alterado, teste_regressao


def _emitir_via_api(tmp_path: Path, sessao_dir: Path, **kwargs) -> Path:
    arquivo_alterado, teste_regressao = _arquivos_pipeline(tmp_path)
    handoff.emitir_handoff(
        sessao_dir=sessao_dir,
        repo_root=tmp_path,
        status=kwargs.get("status", "SUCESSO"),
        codigo_saida=kwargs.get("codigo_saida", 0),
        causa_raiz=CAUSA_RAIZ,
        arquivos_alterados=[arquivo_alterado],
        teste_regressao=teste_regressao,
        gate_status="APROVADO",
        proxima_ferramenta=kwargs.get("proxima_ferramenta", "aidd-tdd"),
        erro=kwargs.get("erro"),
    )
    return sessao_dir / "handoff-diagnose.json"


# ---------------------------------------------------------------------------
# RED: ausência do handoff bloqueia a transição (exit 1)
# ---------------------------------------------------------------------------

def test_handoff_modulo_disponivel():
    assert handoff is not None, "aidd-diagnose/scripts/handoff.py ainda não implementado (RED)"


def test_transicao_bloqueada_sem_handoff_exit_1(tmp_path):
    sessao_dir = _criar_sessao(tmp_path)
    handoff_path = sessao_dir / "handoff-diagnose.json"
    assert not handoff_path.exists()

    resultado = handoff.transicionar_fase(handoff_path, repo_root=tmp_path)
    assert resultado["liberada"] is False
    assert resultado["proxima_fase"] is None
    assert any("ausente" in e for e in resultado["erros"])

    res = _rodar_cli(
        "transicionar", "--handoff", str(handoff_path), "--repo-root", str(tmp_path)
    )
    assert res.returncode == 1, res.stdout + res.stderr
    assert "ausente" in res.stdout


def test_transicao_cli_sem_handoff_resolve_ultima_sessao_e_falha(tmp_path):
    sessao_dir = _criar_sessao(tmp_path)
    res = _rodar_cli("transicionar", "--repo-root", str(tmp_path))
    assert res.returncode == 1, res.stdout + res.stderr
    expected = sessao_dir / "handoff-diagnose.json"
    assert str(expected) in res.stdout or "ausente" in res.stdout


# ---------------------------------------------------------------------------
# GREEN: handoff emitido, assinado, com diagnóstico consolidado e liberado
# ---------------------------------------------------------------------------

def test_emissao_gera_handoff_valido_e_libera_transicao(tmp_path):
    sessao_dir = _criar_sessao(tmp_path)
    handoff_path = _emitir_via_api(tmp_path, sessao_dir)
    dados = json.loads(handoff_path.read_text(encoding="utf-8"))

    assert dados["versao_schema"] == handoff.VERSAO_SCHEMA
    assert dados["ferramenta"] == "aidd-diagnose"
    assert dados["status"] == "SUCESSO"
    assert dados["codigo_saida"] == 0
    assert dados["transicao"]["liberada"] is True
    assert dados["transicao"]["proxima_fase"] == "aidd-tdd"
    assert dados["proxima_ferramenta"] == "aidd-tdd"

    diag = dados["diagnose"]
    assert diag["causa_raiz"] == CAUSA_RAIZ
    assert len(diag["arquivos_alterados"]) == 1
    assert diag["teste_regressao"].endswith("test_modulo_impacto.py")
    assert diag["gate"] == "G_aidd_diagnose"
    assert diag["gate_status"] == "APROVADO"

    assert dados["assinatura"]["algoritmo"] == "sha256"
    assert len(dados["assinatura"]["valor"]) == 64
    assert handoff.verificar_handoff(handoff_path, repo_root=tmp_path) == []

    resultado = handoff.transicionar_fase(handoff_path, repo_root=tmp_path)
    assert resultado == {"liberada": True, "proxima_fase": "aidd-tdd", "erros": []}

    res = _rodar_cli(
        "transicionar", "--handoff", str(handoff_path), "--repo-root", str(tmp_path)
    )
    assert res.returncode == 0, res.stdout + res.stderr
    assert "aidd-tdd" in res.stdout


def test_proxima_ferramenta_aidd_handoff_tambem_libera(tmp_path):
    sessao_dir = _criar_sessao(tmp_path)
    handoff_path = _emitir_via_api(tmp_path, sessao_dir, proxima_ferramenta="aidd-handoff")
    dados = json.loads(handoff_path.read_text(encoding="utf-8"))
    assert dados["proxima_ferramenta"] == "aidd-handoff"
    assert dados["transicao"]["proxima_fase"] == "aidd-handoff"
    assert handoff.transicionar_fase(handoff_path, repo_root=tmp_path)["liberada"] is True


# ---------------------------------------------------------------------------
# Persistência do estado entre fases em sessao.json (Ticket 1)
# ---------------------------------------------------------------------------

def test_estado_persistido_em_sessao_json(tmp_path):
    sessao_dir = _criar_sessao(tmp_path)
    _emitir_via_api(tmp_path, sessao_dir)
    sessao = json.loads((sessao_dir / "sessao.json").read_text(encoding="utf-8"))

    assert sessao["fase_atual"] == 5
    assert sessao["fases_completadas"] == [1, 2, 3, 4, 5]
    assert sessao["status"] == "SUCESSO"
    assert sessao["proxima_ferramenta"] == "aidd-tdd"
    assert sessao["handoff"] == "docs/diagnosticos/%s_regressao-impacto/handoff-diagnose.json" % datetime.date.today().strftime("%Y%m%d")
    assert sessao["emitido_em"]


# ---------------------------------------------------------------------------
# Integridade: adulteração, artefatos, corrupção, falha, proxima ferramenta
# ---------------------------------------------------------------------------

def test_handoff_adulterado_invalida_assinatura(tmp_path):
    sessao_dir = _criar_sessao(tmp_path)
    handoff_path = _emitir_via_api(tmp_path, sessao_dir)
    dados = json.loads(handoff_path.read_text(encoding="utf-8"))
    dados["diagnose"]["gate_status"] = "APROVADO/adulterado"
    handoff_path.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")

    erros = handoff.verificar_handoff(handoff_path, repo_root=tmp_path)
    assert any("Assinatura" in e for e in erros)
    assert handoff.transicionar_fase(handoff_path, repo_root=tmp_path)["liberada"] is False
    assert _rodar_cli("transicionar", "--handoff", str(handoff_path), "--repo-root", str(tmp_path)).returncode == 1


def test_artefato_alterado_apos_handoff_bloqueia_transicao(tmp_path):
    sessao_dir = _criar_sessao(tmp_path)
    handoff_path = _emitir_via_api(tmp_path, sessao_dir)
    dados = json.loads(handoff_path.read_text(encoding="utf-8"))
    alvo = tmp_path / dados["artefatos"][0]["caminho"]
    alvo.write_text(alvo.read_text(encoding="utf-8") + "\n# adulterado", encoding="utf-8")

    erros = handoff.verificar_handoff(handoff_path, repo_root=tmp_path)
    assert any("sha256 divergente" in e for e in erros)
    assert handoff.transicionar_fase(handoff_path, repo_root=tmp_path)["liberada"] is False


def test_artefato_removido_bloqueia_transicao(tmp_path):
    sessao_dir = _criar_sessao(tmp_path)
    handoff_path = _emitir_via_api(tmp_path, sessao_dir)
    dados = json.loads(handoff_path.read_text(encoding="utf-8"))
    (tmp_path / dados["artefatos"][1]["caminho"]).unlink()

    erros = handoff.verificar_handoff(handoff_path, repo_root=tmp_path)
    assert any("não encontrado" in e for e in erros)
    assert handoff.transicionar_fase(handoff_path, repo_root=tmp_path)["liberada"] is False


def test_handoff_corrompido_bloqueia_transicao(tmp_path):
    sessao_dir = _criar_sessao(tmp_path)
    handoff_path = sessao_dir / "handoff-diagnose.json"
    handoff_path.write_text("{ nao e json", encoding="utf-8")

    resultado = handoff.transicionar_fase(handoff_path, repo_root=tmp_path)
    assert resultado["liberada"] is False
    assert any("JSON" in e for e in resultado["erros"])
    assert _rodar_cli("transicionar", "--handoff", str(handoff_path), "--repo-root", str(tmp_path)).returncode == 1


def test_handoff_de_falha_assinado_mas_nao_libera(tmp_path):
    sessao_dir = _criar_sessao(tmp_path)
    arquivo_alterado, teste_regressao = _arquivos_pipeline(tmp_path)
    handoff.emitir_handoff(
        sessao_dir=sessao_dir,
        repo_root=tmp_path,
        status="FALHA",
        codigo_saida=1,
        causa_raiz="Reprodução instável, hipótese não comprovada",
        arquivos_alterados=[arquivo_alterado],
        teste_regressao=teste_regressao,
        gate_status="REPROVADO",
        proxima_ferramenta=None,
        erro="Hipótese descartada após instrumentação; diagnóstico interrompido",
    )
    handoff_path = sessao_dir / "handoff-diagnose.json"

    dados = json.loads(handoff_path.read_text(encoding="utf-8"))
    assert dados["status"] == "FALHA"
    assert dados["transicao"]["liberada"] is False
    assert dados["transicao"]["proxima_fase"] is None
    assert "Hipótese descartada" in dados["erro"]
    assert handoff.verificar_handoff(handoff_path, repo_root=tmp_path) == []

    resultado = handoff.transicionar_fase(handoff_path, repo_root=tmp_path)
    assert resultado["liberada"] is False
    assert any("FALHA" in e for e in resultado["erros"])
    assert _rodar_cli("transicionar", "--handoff", str(handoff_path), "--repo-root", str(tmp_path)).returncode == 1


def test_emissao_sucesso_exige_proxima_ferramenta_valida(tmp_path):
    sessao_dir = _criar_sessao(tmp_path)
    arquivo_alterado, teste_regressao = _arquivos_pipeline(tmp_path)
    with pytest.raises(ValueError):
        handoff.emitir_handoff(
            sessao_dir=sessao_dir,
            repo_root=tmp_path,
            status="SUCESSO",
            codigo_saida=0,
            causa_raiz=CAUSA_RAIZ,
            arquivos_alterados=[arquivo_alterado],
            teste_regressao=teste_regressao,
            proxima_ferramenta="aidd-gpt",  # fora de aidd-tdd|aidd-handoff
        )


def test_campo_diagnose_obrigatorio_reprova_verificacao(tmp_path):
    sessao_dir = _criar_sessao(tmp_path)
    handoff_path = _emitir_via_api(tmp_path, sessao_dir)
    dados = json.loads(handoff_path.read_text(encoding="utf-8"))
    del dados["diagnose"]["teste_regressao"]
    handoff_path.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")

    erros = handoff.verificar_handoff(handoff_path, repo_root=tmp_path)
    assert any("teste_regressao" in e for e in erros)
    assert handoff.transicionar_fase(handoff_path, repo_root=tmp_path)["liberada"] is False


def test_assinatura_hmac_exige_mesma_chave(tmp_path, monkeypatch):
    monkeypatch.setenv(handoff.VAR_CHAVE, "segredo-teste")
    sessao_dir = _criar_sessao(tmp_path)
    handoff_path = _emitir_via_api(tmp_path, sessao_dir)
    dados = json.loads(handoff_path.read_text(encoding="utf-8"))
    assert dados["assinatura"]["algoritmo"] == "hmac-sha256"
    assert handoff.verificar_handoff(handoff_path, repo_root=tmp_path) == []

    monkeypatch.setenv(handoff.VAR_CHAVE, "outra-chave")
    assert any("Assinatura" in e for e in handoff.verificar_handoff(handoff_path, repo_root=tmp_path))

    monkeypatch.delenv(handoff.VAR_CHAVE)
    assert any("chave" in e for e in handoff.verificar_handoff(handoff_path, repo_root=tmp_path))