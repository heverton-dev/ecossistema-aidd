# -*- coding: utf-8 -*-
"""
Teste de Quality Gate Determinístico de Diagnose (Ticket 6 / D13 / DoD 6).
Exige que `gates/G_aidd_diagnose.py` aprove relatórios de causa-raiz válidos
e reprove (exit 1) casos inválidos:
1. Ausência de comando de reprodução determinística (missing repro).
2. Duas ou mais hipóteses ativas simultâneas (two active hypotheses).
3. Teste de regressão ausente ou que não comprove falha antes e passagem depois.
4. Teste de regressão declarado que não existe ou que falha de verdade
   (relatório inventado não passa mais só por auto-declaração).
"""

import json
import subprocess
import sys
from pathlib import Path
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
GATE_SCRIPT = ROOT_DIR / "gates" / "G_aidd_diagnose.py"


def executar_gate_diagnose(caminho_relatorio: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(GATE_SCRIPT), "--relatorio", str(caminho_relatorio)],
        capture_output=True,
        text=True,
        cwd=str(ROOT_DIR),
        encoding="utf-8",
        errors="replace",
    )


def criar_teste(pasta: Path, nome: str, passa: bool = True) -> Path:
    arquivo = pasta / nome
    corpo = "assert 1 + 1 == 2" if passa else "assert 1 + 1 == 3"
    arquivo.write_text(f"def test_regressao():\n    {corpo}\n", encoding="utf-8")
    return arquivo


def relatorio_json_valido(arquivo_teste) -> dict:
    return {
        "comando_reproducao": "pytest tests/repro.py -k test_falha",
        "execucoes_reproducao": 3,
        "resultado_deterministico": True,
        "hipoteses_ativas": ["Hipótese 1: timeout de socket não capturado"],
        "teste_regressao": {"arquivo": str(arquivo_teste), "falhou_antes": True, "passou_depois": True},
    }


def test_bite_reprova_relatorio_inventado_com_teste_inexistente(tmp_path):
    """Morde (exit 1): relatório auto-declarado cujo teste de regressão não existe."""
    relatorio = tmp_path / "relatorio_inventado.json"
    dados = relatorio_json_valido("tests/test_que_nao_existe_xyz.py")
    dados["comando_reproducao"] = "echo inventado"
    relatorio.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")

    res = executar_gate_diagnose(relatorio)
    assert res.returncode == 1
    assert "não existe" in res.stdout


def test_bite_reprova_quando_teste_regressao_falha_de_verdade(tmp_path):
    """Morde (exit 1): 'passou_depois: true' declarado, mas o pytest falha."""
    relatorio = tmp_path / "relatorio_mentiroso.json"
    dados = relatorio_json_valido(criar_teste(tmp_path, "test_vermelho.py", passa=False))
    relatorio.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")

    res = executar_gate_diagnose(relatorio)
    assert res.returncode == 1
    assert "falha agora" in res.stdout


def test_bite_reprova_quando_falta_comando_reproducao(tmp_path):
    """Morde (exit 1): reprova quando não há comando de reprodução comprovado."""
    relatorio = tmp_path / "relatorio_sem_repro.json"
    dados = {
        "comando_reproducao": None,
        "execucoes_reproducao": 0,
        "resultado_deterministico": False,
        "hipoteses_ativas": ["Hipótese 1: erro na desserialização"],
        "teste_regressao": {
            "arquivo": "tests/test_regressao.py",
            "falhou_antes": True,
            "passou_depois": True,
        },
    }
    relatorio.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")

    res = executar_gate_diagnose(relatorio)
    assert res.returncode == 1
    assert "reprodução" in res.stdout.lower() or "repro" in res.stdout.lower()


def test_bite_reprova_quando_duas_hipoteses_ativas(tmp_path):
    """Morde (exit 1): reprova quando há mais de uma hipótese ativa simultaneamente."""
    relatorio = tmp_path / "relatorio_duas_hipoteses.json"
    dados = {
        "comando_reproducao": "pytest tests/repro.py -k test_falha",
        "execucoes_reproducao": 3,
        "resultado_deterministico": True,
        "hipoteses_ativas": [
            "Hipótese 1: timeout de socket",
            "Hipótese 2: estouro de buffer de memória",
        ],
        "teste_regressao": {
            "arquivo": "tests/test_regressao.py",
            "falhou_antes": True,
            "passou_depois": True,
        },
    }
    relatorio.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")

    res = executar_gate_diagnose(relatorio)
    assert res.returncode == 1
    assert "hipótese" in res.stdout.lower() or "hypothesis" in res.stdout.lower()


def test_bite_reprova_quando_falta_teste_regressao(tmp_path):
    """Morde (exit 1): reprova quando falta teste de regressão ou não provou falha/sucesso."""
    relatorio = tmp_path / "relatorio_sem_regressao.json"
    dados = {
        "comando_reproducao": "pytest tests/repro.py -k test_falha",
        "execucoes_reproducao": 3,
        "resultado_deterministico": True,
        "hipoteses_ativas": [
            "Hipótese 1: timeout de socket",
        ],
        "teste_regressao": None,
    }
    relatorio.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")

    res = executar_gate_diagnose(relatorio)
    assert res.returncode == 1
    assert "regressão" in res.stdout.lower() or "regression" in res.stdout.lower()


def test_aprova_relatorio_valido_json(tmp_path):
    """Caminho feliz (exit 0): aprova relatório estruturado JSON com todos os critérios satisfeitos."""
    relatorio = tmp_path / "relatorio_valido.json"
    dados = {
        "comando_reproducao": "pytest tests/repro.py -k test_falha",
        "execucoes_reproducao": 3,
        "resultado_deterministico": True,
        "hipoteses_ativas": [
            "Hipótese 1: timeout de socket não capturado",
        ],
        "hipoteses_descartadas": [
            {"hipotese": "Hipótese preliminar 0: DNS inválido", "prova": "DNS resolvido com sucesso"}
        ],
        "teste_regressao": {
            "arquivo": str(criar_teste(tmp_path, "test_regressao.py")),
            "falhou_antes": True,
            "passou_depois": True,
        },
    }
    relatorio.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")

    res = executar_gate_diagnose(relatorio)
    assert res.returncode == 0
    assert "APROVADO" in res.stdout or "EXIT 0" in res.stdout


def test_aprova_relatorio_valido_markdown(tmp_path):
    """Caminho feliz (exit 0): aprova relatório em formato Markdown (RELATORIO-CAUSA-RAIZ.md)."""
    relatorio = tmp_path / "RELATORIO-CAUSA-RAIZ.md"
    conteudo = """# RELATORIO-CAUSA-RAIZ

## Resumo Executivo
Análise de diagnose realizada com isolamento de falha.

## Fases Executadas

### Fase 1: Reprodução Determinística
- **Status**: CONCLUIDA
- **Comando**: `pytest tests/repro.py -k test_falha`
- **Execuções**: 3 execuções com o mesmo resultado determinístico
- **Resultado Determinístico**: Sim (100%)

### Fase 3: Hipótese Ativa
- **Status**: CONCLUIDA
**Hipóteses Ativas**:
  - Falha de serialização JSON ao manipular campos datetime sem encoder

**Hipóteses Descartadas**:
  - Falha de rede: Conexão local em loopback sem perda de pacotes

### Fase 5: Teste de Regressão e Correção Cirúrgica
- **Status**: CONCLUIDA
- **Teste de Regressão**: `test_regressao_diagnose.py`
- **Resultado Antes do Fix**: FALHA (exit 1)
- **Resultado Após o Fix**: PASSOU (exit 0)
"""
    criar_teste(tmp_path, "test_regressao_diagnose.py")
    relatorio.write_text(conteudo, encoding="utf-8")

    res = executar_gate_diagnose(relatorio)
    assert res.returncode == 0
    assert "APROVADO" in res.stdout or "EXIT 0" in res.stdout
