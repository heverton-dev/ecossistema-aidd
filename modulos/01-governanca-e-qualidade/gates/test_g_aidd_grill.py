# -*- coding: utf-8 -*-
"""
Teste de Quality Gate Determinístico de Entrevista Socrática (Ticket 7 / Lei #13).
Comprova que G_aidd_grill.py aprova rodadas íntegras (exit 0) e morde (exit 1) diante de:
1. Perguntas sem numeração explícita.
2. Recomendações sem justificativa técnica causal (porque, pois, etc.).
3. Arquivo inexistente ou sem perguntas.
"""

import subprocess
import sys
from pathlib import Path
import pytest

ROOT = next((p.parent for p in Path(__file__).resolve().parents if p.name == "modulos"), Path(__file__).resolve().parent.parent)  # raiz: pai de modulos/ (VSA) ou de gates/ (árvore sintética)
GATE = ROOT / "modulos" / "01-governanca-e-qualidade" / "gates" / "G_aidd_grill.py"


def executar_gate(arquivo_path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(GATE), "--arquivo", str(arquivo_path)],
        capture_output=True,
        text=True,
        cwd=str(ROOT)
    )


RODADA_VALIDA = """
# Rodada Socrática 1: Definição de Autenticação

### 1. Qual estratégia de sessão devemos adotar para os usuários da API?
- (A) JWT stateless com rotação de refresh token
- (B) Sessão stateful via Redis
**Recomendado:** Opção A, porque simplifica a escalabilidade horizontal e elimina dependência externa de cache.

### 2. Como devemos tratar requisições não autenticadas em rotas públicas?
- (A) Permitir acesso anônimo transparente
- (B) Exigir token de visitante
**Recomendado:** Opção A, pois reduz a latência e não onera o handshake inicial.
"""


def test_gate_grill_aprova_rodada_integra(tmp_path):
    arq = tmp_path / "rodada_ok.md"
    arq.write_text(RODADA_VALIDA, encoding="utf-8")

    res = executar_gate(arq)
    assert res.returncode == 0
    assert "APROVADO" in res.stdout


def test_gate_grill_morde_se_pergunta_sem_numeracao(tmp_path):
    conteudo_sem_numero = """
# Rodada Sem Numeração
### Qual banco de dados usar?
- (A) Postgres
- (B) SQLite
**Recomendado:** SQLite, porque é local.
"""
    arq = tmp_path / "rodada_sem_numero.md"
    arq.write_text(conteudo_sem_numero, encoding="utf-8")

    res = executar_gate(arq)
    assert res.returncode == 1
    assert "Nenhuma pergunta numerada" in res.stdout


def test_gate_grill_morde_se_recomendacao_sem_justificativa(tmp_path):
    conteudo_sem_motivo = """
# Rodada Sem Justificativa
### 1. Qual banco usar?
- (A) Postgres
- (B) SQLite
**Recomendado:** Opção A.
"""
    arq = tmp_path / "rodada_sem_justificativa.md"
    arq.write_text(conteudo_sem_motivo, encoding="utf-8")

    res = executar_gate(arq)
    assert res.returncode == 1
    assert "falta de justificativa causal técnica" in res.stdout


def test_gate_grill_morde_se_arquivo_inexistente(tmp_path):
    arq = tmp_path / "inexistente.md"
    res = executar_gate(arq)
    assert res.returncode == 1
    assert "não existe" in res.stdout
