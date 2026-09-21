# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — TESTE DO COMPILADOR DE TICKETS DE PLANO (ISSUE-PIPE-0004)
=============================================================================
Validação determinística de conformidade (Leis #1, #2, #5, #13):
  1. Compilação de plano fixture completo em manifesto handoff_evolution.json.
  2. Validação direta do JSON gerado contra gates/G_PIPELINE_HANDOFF.py (exit 0).
  3. Particionamento correto entre fase paralela (sem dependências e arquivos disjuntos)
     e fase sequencial (dependentes ou arquivos colidentes).
  4. Reprovação com exit 1 quando há ciclos no grafo de dependências (DAG).
  5. Reprovação com exit 1 quando comandos de validação estão ausentes ou triviais.
  6. Reprovação com exit 1 quando arquivos alvo estão vazios ou ausentes.
  7. Execução via CLI real via subprocess.
=============================================================================
"""

import json
import subprocess
import sys
from pathlib import Path
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
COMPILADOR_SCRIPT = ROOT_DIR / "scripts" / "compilador_tickets_plano.py"
GATE_SCRIPT = ROOT_DIR / "gates" / "G_PIPELINE_HANDOFF.py"


def executar_compilador_cli(*args: str) -> subprocess.CompletedProcess:
    """Executa o compilador de tickets via subprocess real."""
    cmd = [sys.executable, str(COMPILADOR_SCRIPT), *args]
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(ROOT_DIR),
        encoding="utf-8",
        errors="replace",
    )


def criar_fixture_plano_valido(pasta_base: Path) -> Path:
    """Cria um diretório de plano válido com tickets no formato /aidd-tickets."""
    pasta_plano = pasta_base / "PLAN-0099-teste-compilador"
    pasta_plano.mkdir(parents=True, exist_ok=True)

    # 00-PROCESSO-E-DECISOES.md
    decisoes_md = """# PROCESSO E DECISOES — teste-compilador

> **Origem:** Planejamento estruturado no monorepo ecossistema-aidd.
> **Proposito deste arquivo:** Registro unico do processo e governanca desta iniciativa.

## 1. O que este esforco busca
- **Objetivo Principal:** Testar compilacao deterministica de tickets para handoff
"""
    (pasta_plano / "00-PROCESSO-E-DECISOES.md").write_text(decisoes_md, encoding="utf-8")

    # 01-modulo-auth.md (contém 2 tickets: 1 paralelo e 1 dependente)
    item1_md = """# Item 1 — Modulo de Autenticacao

### [TICKET-01] Implementar camada de autenticacao
- **Target Files:**
  - `scripts/auth_helper.py`
  - `tests/test_auth_helper.py`
- **Validation Command:** `pytest tests/test_auth_helper.py`
- **Blocked By:** []
- **Comando Red:** `pytest tests/test_auth_helper.py`
- **Comando Green:** `pytest tests/test_auth_helper.py`
- **Isolamento:** `git-worktree`

### [TICKET-02] Adicionar tokens JWT na autenticacao
- **Target Files:**
  - `scripts/auth_helper.py`
- **Validation Command:** `pytest tests/test_auth_jwt.py`
- **Blocked By:** [TICKET-01]
- **Isolamento:** `processo-isolado`
"""
    (pasta_plano / "01-modulo-auth.md").write_text(item1_md, encoding="utf-8")

    # 02-modulo-metrics.md (contém 1 ticket paralelo com arquivos disjuntos)
    item2_md = """# Item 2 — Modulo de Metricas

### [TICKET-03] Implementar coletor de metricas
- **Target Files:**
  - `scripts/metrics_collector.py`
  - `tests/test_metrics.py`
- **Validation Command:** `pytest tests/test_metrics.py`
- **Blocked By:** []
- **Isolamento:** `git-worktree`
"""
    (pasta_plano / "02-modulo-metrics.md").write_text(item2_md, encoding="utf-8")

    return pasta_plano


def test_compilacao_plano_fixture_valido(tmp_path):
    """Testa a compilação completa de uma fixture real de plano gerando JSON conforme."""
    pasta_plano = criar_fixture_plano_valido(tmp_path)
    output_json = pasta_plano / "handoff_evolution.json"

    res = executar_compilador_cli("--plano", str(pasta_plano))
    assert res.returncode == 0, f"Deveria compilar com exit 0, falhou:\n{res.stdout}\n{res.stderr}"
    assert output_json.is_file(), "Arquivo handoff_evolution.json não foi gerado."

    conteudo = json.loads(output_json.read_text(encoding="utf-8"))

    # Verifica estrutura
    assert conteudo["versao_schema"] == "1.0.0"
    assert conteudo["origem_plano"] == "evolucao"
    assert conteudo["fluxo_alvo"] == "evolution"
    assert conteudo["meta"]["nome_projeto"] == "teste-compilador"
    assert conteudo["meta"]["iniciativa_id"] == "PLAN-0099"

    # Particionamento:
    # TICKET-01 e TICKET-03 não têm blocked_by e têm arquivos disjuntos -> fase_paralela_assincrona
    # TICKET-02 depende de TICKET-01 -> fase_sequencial_sincrona
    paralelos = [t["id"] for t in conteudo["fase_paralela_assincrona"]]
    sequenciais = [t["id"] for t in conteudo["fase_sequencial_sincrona"]]

    assert "TICKET-01" in paralelos
    assert "TICKET-03" in paralelos
    assert "TICKET-02" in sequenciais
    assert conteudo["barreira_sincronizacao"] == ["gates/G_SAIDA_BINARIA.py"]

    # Validação formal com G_PIPELINE_HANDOFF
    gate_res = subprocess.run(
        [sys.executable, str(GATE_SCRIPT), "--manifesto", str(output_json)],
        capture_output=True,
        text=True,
        cwd=str(ROOT_DIR),
        encoding="utf-8",
        errors="replace",
    )
    assert gate_res.returncode == 0, f"Quality gate reprovou manifesto:\n{gate_res.stdout}\n{gate_res.stderr}"


def test_sobreposicao_de_arquivos_move_candidato_para_sequencial(tmp_path):
    """
    Testa que se dois tickets têm blocked_by: [], mas compartilham arquivos_alvo,
    o segundo é transferido para a fase sequencial síncrona para evitar conflitos de merge.
    """
    pasta_plano = tmp_path / "PLAN-0098-colisao-arquivos"
    pasta_plano.mkdir(parents=True, exist_ok=True)

    (pasta_plano / "00-PROCESSO-E-DECISOES.md").write_text(
        "# PROCESSO E DECISOES — colisao-arquivos\n\n## 1. O que este esforco busca\n- **Objetivo Principal:** Testar desambiguacao de arquivos\n",
        encoding="utf-8",
    )

    item_md = """# Item 1 — Conflito de Arquivos

### [TICKET-01] Criar modulo core
- **Target Files:** `scripts/core_engine.py`
- **Validation Command:** `pytest tests/test_core.py`
- **Blocked By:** []

### [TICKET-02] Estender modulo core
- **Target Files:** `scripts/core_engine.py`
- **Validation Command:** `pytest tests/test_core_ext.py`
- **Blocked By:** []
"""
    (pasta_plano / "01-conflito.md").write_text(item_md, encoding="utf-8")

    res = executar_compilador_cli("--plano", str(pasta_plano))
    assert res.returncode == 0, f"Falha na compilação:\n{res.stdout}\n{res.stderr}"

    output_json = pasta_plano / "handoff_evolution.json"
    conteudo = json.loads(output_json.read_text(encoding="utf-8"))

    paralelos = [t["id"] for t in conteudo.get("fase_paralela_assincrona", [])]
    sequenciais = [t["id"] for t in conteudo.get("fase_sequencial_sincrona", [])]

    # Somente 1 deve estar no paralelo, o outro vai para sequencial
    assert len(paralelos) == 1
    assert "TICKET-01" in paralelos
    assert "TICKET-02" in sequenciais


def test_reprova_ciclo_no_grafo_dag(tmp_path):
    """Testa que ciclos no grafo de dependências causam saída com exit 1."""
    pasta_plano = tmp_path / "PLAN-0097-ciclo"
    pasta_plano.mkdir(parents=True, exist_ok=True)

    (pasta_plano / "00-PROCESSO-E-DECISOES.md").write_text(
        "# PROCESSO E DECISOES — ciclo\n\n## 1. O que este esforco busca\n- **Objetivo Principal:** Teste de ciclo de dependencia\n",
        encoding="utf-8",
    )

    item_md = """# Item 1 — Ciclo

### [TICKET-01] Tarefa 1
- **Target Files:** `scripts/a.py`
- **Validation Command:** `pytest tests/test_a.py`
- **Blocked By:** [TICKET-02]

### [TICKET-02] Tarefa 2
- **Target Files:** `scripts/b.py`
- **Validation Command:** `pytest tests/test_b.py`
- **Blocked By:** [TICKET-01]
"""
    (pasta_plano / "01-ciclo.md").write_text(item_md, encoding="utf-8")

    res = executar_compilador_cli("--plano", str(pasta_plano))
    assert res.returncode == 1, f"Deveria falhar com exit 1 por ciclo, retornou {res.returncode}"
    assert "Ciclo não resolvível detectado" in res.stdout or "Ciclo" in res.stderr


def test_reprova_comando_validacao_ausente(tmp_path):
    """Testa que a ausência de comando de validação causa reprovação imediata (exit 1)."""
    pasta_plano = tmp_path / "PLAN-0096-sem-comando"
    pasta_plano.mkdir(parents=True, exist_ok=True)

    (pasta_plano / "00-PROCESSO-E-DECISOES.md").write_text(
        "# PROCESSO E DECISOES — sem-comando\n\n## 1. O que este esforco busca\n- **Objetivo Principal:** Teste sem comando\n",
        encoding="utf-8",
    )

    item_md = """# Item 1 — Sem comando

### [TICKET-01] Tarefa incompleta
- **Target Files:** `scripts/a.py`
- **Blocked By:** []
"""
    (pasta_plano / "01-incompleto.md").write_text(item_md, encoding="utf-8")

    res = executar_compilador_cli("--plano", str(pasta_plano))
    assert res.returncode == 1, f"Deveria falhar com exit 1, retornou {res.returncode}"
    assert "Ausência de comando de validação" in res.stdout or "comando" in res.stderr


def test_reprova_comando_validacao_trivial(tmp_path):
    """Testa que comando de validação trivial (ex: exit 0 ou echo ok) é reprovado como stub."""
    pasta_plano = tmp_path / "PLAN-0095-comando-trivial"
    pasta_plano.mkdir(parents=True, exist_ok=True)

    (pasta_plano / "00-PROCESSO-E-DECISOES.md").write_text(
        "# PROCESSO E DECISOES — comando-trivial\n\n## 1. O que este esforco busca\n- **Objetivo Principal:** Teste comando trivial\n",
        encoding="utf-8",
    )

    item_md = """# Item 1 — Comando trivial

### [TICKET-01] Tarefa com stub de validacao
- **Target Files:** `scripts/a.py`
- **Validation Command:** `exit 0`
- **Blocked By:** []
"""
    (pasta_plano / "01-trivial.md").write_text(item_md, encoding="utf-8")

    res = executar_compilador_cli("--plano", str(pasta_plano))
    assert res.returncode == 1, f"Deveria falhar com exit 1 por comando trivial, retornou {res.returncode}"
    assert "trivial" in res.stdout or "stub" in res.stdout


def test_reprova_arquivos_alvo_ausentes(tmp_path):
    """Testa que ausência de arquivos alvo causa reprovação com exit 1."""
    pasta_plano = tmp_path / "PLAN-0094-sem-alvos"
    pasta_plano.mkdir(parents=True, exist_ok=True)

    (pasta_plano / "00-PROCESSO-E-DECISOES.md").write_text(
        "# PROCESSO E DECISOES — sem-alvos\n\n## 1. O que este esforco busca\n- **Objetivo Principal:** Teste sem alvos\n",
        encoding="utf-8",
    )

    item_md = """# Item 1 — Sem alvos

### [TICKET-01] Tarefa sem arquivos alvo
- **Validation Command:** `pytest tests/test_x.py`
- **Blocked By:** []
"""
    (pasta_plano / "01-sem-alvos.md").write_text(item_md, encoding="utf-8")

    res = executar_compilador_cli("--plano", str(pasta_plano))
    assert res.returncode == 1, f"Deveria falhar com exit 1 por falta de alvos, retornou {res.returncode}"
    assert "arquivos alvo vazia" in res.stdout or "alvo" in res.stdout
