# -*- coding: utf-8 -*-
"""
Teste de Output Consolidado e Handoff Estruturado (Ticket 8 / D15 / DoD 2, 7, 8).

Red: pipeline executado por completo sem `handoff-melhoria.json` deve FALHAR a transição.
Green: handoff emitido, assinado (sha256 canônico ou HMAC), com artefatos hasheados,
consumível pelo orquestrador (gate G_HANDOFF_MELHORIA) para transitar melhoria -> plan.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
SKILL_SCRIPTS = ROOT_DIR / ".agents" / "skills" / "aidd-melhoria" / "scripts"
GATE = ROOT_DIR / "gates" / "G_HANDOFF_MELHORIA.py"

if str(SKILL_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SKILL_SCRIPTS))

import cli  # noqa: E402
import handoff  # noqa: E402

MANIFESTO_VALIDO = {
    "pedido": "Consolidar handoff estruturado da melhoria",
    "nome": "consolidar-handoff-estruturado",
    "nota_atual": "5.0",
    "evidencia": "cli.py emitia handoff sem assinatura nem lista de artefatos",
    "resumo": "Handoff passa a ser assinado e consumivel pelo orquestrador",
    "achados": ["Handoff sem assinatura", "Caminho init nao emitia handoff"],
    "riscos": ["Consumidores antigos que ignoram o campo assinatura"],
    "recomendacao": "Adotar o schema handoff-melhoria 1.0.0",
    "itens_avaliados": [
        {"item": "Assinatura", "status": "nao-feito", "justificativa": "Inexistente antes do ticket 8"}
    ],
}


def _executar_pipeline(tmp_path: Path) -> Path:
    """Executa o pipeline completo (manifesto -> relatório -> handoff) isolado em tmp_path."""
    manifesto = tmp_path / "manifesto.json"
    manifesto.write_text(json.dumps(MANIFESTO_VALIDO, ensure_ascii=False), encoding="utf-8")
    destino = tmp_path / "handoff-melhoria.json"
    codigo = cli.processar_manifesto(manifesto, repo_root=tmp_path, handoff_path=destino)
    assert codigo == 0
    return destino


def _rodar_gate(handoff_path: Path, repo_root: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(GATE), "--handoff", str(handoff_path), "--repo-root", str(repo_root)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )


# ---------------------------------------------------------------------------
# RED: ausência do handoff bloqueia a transição
# ---------------------------------------------------------------------------

def test_pipeline_completo_sem_handoff_falha_transicao(tmp_path):
    destino = _executar_pipeline(tmp_path)
    destino.unlink()

    resultado = handoff.transicionar_fase(destino, repo_root=tmp_path)
    assert resultado["liberada"] is False
    assert resultado["proxima_fase"] is None
    assert any("ausente" in e for e in resultado["erros"])

    res = _rodar_gate(destino, tmp_path)
    assert res.returncode == 1, res.stdout + res.stderr
    assert "ausente" in res.stdout


# ---------------------------------------------------------------------------
# GREEN: handoff emitido, assinado e consumível
# ---------------------------------------------------------------------------

def test_pipeline_completo_emite_handoff_assinado_e_libera_plan(tmp_path):
    destino = _executar_pipeline(tmp_path)
    dados = json.loads(destino.read_text(encoding="utf-8"))

    assert dados["versao_schema"] == handoff.VERSAO_SCHEMA
    assert dados["ferramenta"] == "aidd-melhoria"
    assert dados["status"] == "SUCESSO"
    assert dados["codigo_saida"] == 0
    assert dados["transicao"] == {
        "fase_atual": "melhoria",
        "proxima_fase": "plan",
        "liberada": True,
        "requer_aprovacao_humana": True,
    }
    assert dados["assinatura"]["algoritmo"] == "sha256"
    assert len(dados["assinatura"]["valor"]) == 64

    slug = f"{date.today().strftime('%d-%m-%Y')}_melhoria-consolidar-handoff-estruturado"
    caminhos = sorted(a["caminho"] for a in dados["artefatos"])
    assert caminhos == [f"docs/melhorias/{slug}.html", f"docs/melhorias/{slug}.json"]
    for artefato in dados["artefatos"]:
        assert (tmp_path / artefato["caminho"]).is_file()
        assert len(artefato["sha256"]) == 64

    assert handoff.verificar_handoff(destino, repo_root=tmp_path) == []
    resultado = handoff.transicionar_fase(destino, repo_root=tmp_path)
    assert resultado == {"liberada": True, "proxima_fase": "plan", "erros": []}

    res = _rodar_gate(destino, tmp_path)
    assert res.returncode == 0, res.stdout + res.stderr
    assert "plan" in res.stdout


def test_handoff_adulterado_invalida_assinatura(tmp_path):
    destino = _executar_pipeline(tmp_path)
    dados = json.loads(destino.read_text(encoding="utf-8"))
    dados["detalhes"]["nota_atual"] = "10"
    destino.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")

    erros = handoff.verificar_handoff(destino, repo_root=tmp_path)
    assert any("Assinatura" in e for e in erros)
    assert handoff.transicionar_fase(destino, repo_root=tmp_path)["liberada"] is False
    assert _rodar_gate(destino, tmp_path).returncode == 1


def test_artefato_alterado_apos_handoff_bloqueia_transicao(tmp_path):
    destino = _executar_pipeline(tmp_path)
    dados = json.loads(destino.read_text(encoding="utf-8"))
    alvo = tmp_path / dados["artefatos"][0]["caminho"]
    alvo.write_text(alvo.read_text(encoding="utf-8") + "\nadulterado", encoding="utf-8")

    erros = handoff.verificar_handoff(destino, repo_root=tmp_path)
    assert any("sha256 divergente" in e for e in erros)
    assert handoff.transicionar_fase(destino, repo_root=tmp_path)["liberada"] is False


def test_artefato_removido_bloqueia_transicao(tmp_path):
    destino = _executar_pipeline(tmp_path)
    dados = json.loads(destino.read_text(encoding="utf-8"))
    (tmp_path / dados["artefatos"][1]["caminho"]).unlink()

    erros = handoff.verificar_handoff(destino, repo_root=tmp_path)
    assert any("não encontrado" in e for e in erros)


def test_handoff_corrompido_bloqueia_transicao(tmp_path):
    destino = tmp_path / "handoff-melhoria.json"
    destino.write_text("{ nao e json", encoding="utf-8")
    resultado = handoff.transicionar_fase(destino, repo_root=tmp_path)
    assert resultado["liberada"] is False
    assert any("JSON" in e for e in resultado["erros"])


def test_handoff_sem_campo_obrigatorio_reprova_schema(tmp_path):
    destino = _executar_pipeline(tmp_path)
    dados = json.loads(destino.read_text(encoding="utf-8"))
    del dados["transicao"]
    destino.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
    erros = handoff.verificar_handoff(destino, repo_root=tmp_path)
    assert any("transicao" in e for e in erros)


def test_handoff_de_falha_e_assinado_mas_nao_libera(tmp_path):
    destino = tmp_path / "handoff-melhoria.json"
    codigo = cli.processar_manifesto(tmp_path / "inexistente.json", repo_root=tmp_path, handoff_path=destino)
    assert codigo == 1

    dados = json.loads(destino.read_text(encoding="utf-8"))
    assert dados["status"] == "FALHA"
    assert dados["transicao"]["liberada"] is False
    assert dados["transicao"]["proxima_fase"] is None
    assert "Manifesto não encontrado" in dados["erro"]
    assert handoff.verificar_handoff(destino, repo_root=tmp_path) == []

    resultado = handoff.transicionar_fase(destino, repo_root=tmp_path)
    assert resultado["liberada"] is False
    assert any("FALHA" in e for e in resultado["erros"])
    assert _rodar_gate(destino, tmp_path).returncode == 1


def test_sucesso_fallback_nao_libera_transicao_automatica(tmp_path):
    import fallback

    def motor_quebrado():
        raise fallback.LLMTimeoutError("timeout simulado")

    destino = tmp_path / "handoff-melhoria.json"
    fallback.executar_analise_com_fallback(
        motor_quebrado, pedido="x", nome="y", handoff_path=destino, max_tentativas=1, backoff_base=0,
    )
    dados = json.loads(destino.read_text(encoding="utf-8"))
    assert dados["status"] == "SUCESSO_FALLBACK"
    assert dados["transicao"]["liberada"] is False
    assert handoff.verificar_handoff(destino, repo_root=tmp_path) == []
    assert handoff.transicionar_fase(destino, repo_root=tmp_path)["liberada"] is False


def test_assinatura_hmac_exige_mesma_chave(tmp_path, monkeypatch):
    monkeypatch.setenv(handoff.VAR_CHAVE, "segredo-teste")
    destino = _executar_pipeline(tmp_path)
    dados = json.loads(destino.read_text(encoding="utf-8"))
    assert dados["assinatura"]["algoritmo"] == "hmac-sha256"
    assert handoff.verificar_handoff(destino, repo_root=tmp_path) == []

    monkeypatch.setenv(handoff.VAR_CHAVE, "outra-chave")
    assert any("Assinatura" in e for e in handoff.verificar_handoff(destino, repo_root=tmp_path))

    monkeypatch.delenv(handoff.VAR_CHAVE)
    assert any("chave" in e for e in handoff.verificar_handoff(destino, repo_root=tmp_path))


def test_caminho_init_tambem_emite_handoff(tmp_path, monkeypatch):
    import gerenciador_melhorias as gm

    monkeypatch.setattr(gm, "DOCS_MELHORIAS", tmp_path / "docs" / "melhorias")
    destino = tmp_path / "handoff-melhoria.json"
    codigo = cli.main([
        "init", "--pedido", "Melhorar handoff via subcomando init",
        "--nome", "handoff-via-init", "--handoff", str(destino),
    ])
    assert codigo == 0
    dados = json.loads(destino.read_text(encoding="utf-8"))
    assert dados["status"] == "SUCESSO"
    assert len(dados["artefatos"]) == 2
    assert handoff.verificar_handoff(destino, repo_root=tmp_path) == []
