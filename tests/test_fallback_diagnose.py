# -*- coding: utf-8 -*-
"""
Testes do Ticket 4 (D11 / DoD 4) - Fallback Operacional sem MCP para aidd-diagnose.

Exige o entregavel .agents/skills/aidd-diagnose/scripts/fallback.py:
- Probe de conexao ao MCP code-review-graph com retry + backoff exponencial
  (servidor sobe a frio em ~11,3 s; CONNECT_TIMEOUT de 30 s observado em 2026-09-23).
- Com o MCP indisponivel, a Fase 2 CONCLUI via fallback deterministico no
  espirito de Grep/Glob/Read (stdlib exclusivamente):
    * callers = busca pelo nome da funcao (AST em todos os .py do repo);
    * callees = leitura do corpo da funcao (AST);
    * impacto = busca de imports (quem importa o modulo do arquivo suspeito).
- O modo usado pela Fase 2 e registrado em sessao.json ('fallback' ou 'grafo').
"""

import importlib.util
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
SCRIPT = ROOT_DIR / ".agents" / "skills" / "aidd-diagnose" / "scripts" / "fallback.py"


def carregar_fallback():
    """Importa fallback.py do entregavel (mesmo padrao de test_cobertura_grafo)."""
    spec = importlib.util.spec_from_file_location("aidd_diagnose_fallback", str(SCRIPT))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _escrever_projeto(repo: Path) -> Path:
    """Mini-repo deterministico com 3 arquivos .py e uma sessao de diagnose."""
    pkg = repo / "servicos"
    pkg.mkdir(parents=True)
    (repo / "app.py").write_text(
        "from servicos import pagamento\n"
        "\n"
        "def main():\n"
        "    total = pagamento.calcular_total(10)\n"
        "    return total\n"
        "\n"
        "if __name__ == '__main__':\n"
        "    main()\n",
        encoding="utf-8",
    )
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "pagamento.py").write_text(
        "import json\n"
        "from . import impostos\n"
        "\n"
        "def calcular_total(base):\n"
        "    extra = impostos.calcular(base)\n"
        "    return base + extra\n",
        encoding="utf-8",
    )
    (pkg / "impostos.py").write_text(
        "def calcular(base):\n"
        "    return base * 0.1\n",
        encoding="utf-8",
    )
    diag = repo / "docs" / "diagnosticos" / "20260924_falha-conexao-banco"
    diag.mkdir(parents=True)
    sessao = diag / "sessao.json"
    sessao.write_text(
        json.dumps({
            "sintoma": "falha conexao banco",
            "data_inicio": "2026-09-24T00:00:00.000000",
            "fase_atual": 1,
            "fases_completadas": [1],
        }, ensure_ascii=False),
        encoding="utf-8",
    )
    return sessao


class TestEntregavel:
    """O modulo fallback.py existe e expoe a API de resiliencia da Fase 2."""

    def test_modulo_importa_e_expoe_api(self):
        mod = carregar_fallback()
        for nome in (
            "analisar_fase2",
            "probe_mcp_com_retry",
            "registrar_modo_fase2",
            "buscar_chamadores",
            "buscar_callees",
            "busca_impacto_imports",
            "main",
        ):
            assert callable(getattr(mod, nome)), f"{nome} ausente"

    def test_retry_backoff_padrao_suporta_cold_start_de_11s(self):
        """Backoff padrao deve acumular ao menos ~11 s esperando o servidor subir."""
        mod = carregar_fallback()
        assert mod.PROBE_MAX_TENTATIVAS >= 3
        soma = 0.0
        for i in range(1, mod.PROBE_MAX_TENTATIVAS):
            soma += mod.PROBE_BACKOFF_BASE * (mod.PROBE_FATOR ** (i - 1))
        assert soma >= 11.0, f"backoff acumulado {soma:.1f}s < cold start de ~11s"


class TestMCPIndisponivelFallback:
    """Com o MCP derrubado, a Fase 2 conclui via fallback e registra o modo."""

    @pytest.fixture()
    def mcp_fora(self):
        """Estado 'MCP down': o probe levanta FileNotFoundError em TODAS as tentativas."""
        chamadas = {"probes": 0}

        def _mcp_fora(_raiz, _arquivo):
            chamadas["probes"] += 1
            raise FileNotFoundError("code-review-graph ausente no PATH (MCP indisponivel)")

        return _mcp_fora, chamadas

    def test_mcp_fora_fase2_conclui_via_fallback_e_registra_modo(self, tmp_path, monkeypatch, mcp_fora):
        mod = carregar_fallback()
        repo = tmp_path / "repo"
        repo.mkdir()
        sessao = _escrever_projeto(repo)
        mcp_fora, chamadas = mcp_fora
        esperas = []
        monkeypatch.setattr(mod, "_rodar_probe", mcp_fora)
        monkeypatch.setattr(mod, "_sono", lambda s: esperas.append(s))

        resultado = mod.analisar_fase2(
            raiz=repo,
            arquivos=["servicos/pagamento.py"],
            funcao="calcular_total",
            sessao=sessao,
        )

        assert resultado["status"] == "ok"
        assert resultado["modo_fase2"] == "fallback", "MCP fora deveria operar em modo fallback"
        assert chamadas["probes"] == mod.PROBE_MAX_TENTATIVAS, "retry esgotado"
        assert len(esperas) == mod.PROBE_MAX_TENTATIVAS - 1, "backoff entre tentativas"
        assert resultado["probe"]["ok"] is False

        analise = resultado["analise"]
        arq = analise["arquivos"]["servicos/pagamento.py"]
        assert arq["imports"], "imports extraidos por leitura (Read)"
        assert "calcular_total" in arq["funcoes_definidas"]

        # callees = leitura do corpo da funcao (AST).
        callees = {c["nome"] for c in arq["funcoes_definidas"]["calcular_total"]["callees"]}
        assert "calcular" in callees, f"callees por corpo ausentes: {callees}"

        # callers = busca pelo nome da funcao entre os .py do repo.
        assert any(c["arquivo"] == "app.py" for c in analise["chamadores"])

        # impacto = busca de imports (quem importa o modulo suspeito).
        importadores = analise["impacto_imports"]["servicos/pagamento.py"]
        assert any(i["arquivo"] == "app.py" for i in importadores)

        dados = json.loads(sessao.read_text(encoding="utf-8"))
        assert dados["fase2"]["modo"] == "fallback", "modo nao registrado na sessao"
        assert dados["fase2"]["detalhes"]["probe"]["ok"] is False

    def test_main_cli_exit_0_completa_fase2_via_fallback(self, tmp_path, monkeypatch, mcp_fora):
        mod = carregar_fallback()
        repo = tmp_path / "repo"
        repo.mkdir()
        sessao = _escrever_projeto(repo)
        mcp_fora, _ = mcp_fora
        monkeypatch.setattr(mod, "_rodar_probe", mcp_fora)
        monkeypatch.setattr(mod, "_sono", lambda s: None)

        codigo = mod.main([
            "analisar", "--repo", str(repo),
            "--arquivos", "servicos/pagamento.py",
            "--funcao", "calcular_total",
            "--sessao", str(sessao),
        ])
        assert codigo == 0, "Fase 2 concluiu via fallback com exit 0"


class TestColdStartGrafo:
    """Cold start: servidor acorda entre tentativas -> MCP sobe, modo grafo."""

    def test_probe_falha_2x_e_sobe_na_3_retorna_modo_grafo(self, tmp_path, monkeypatch):
        mod = carregar_fallback()
        repo = tmp_path / "repo"
        repo.mkdir()
        sessao = _escrever_projeto(repo)
        tenta = {"n": 0}
        esperas = []

        def _acorda_na_terceira(_raiz, _arquivo):
            tenta["n"] += 1
            if tenta["n"] < 3:
                raise FileNotFoundError("cold start ainda subindo")
            return subprocess.CompletedProcess(
                args=[], returncode=0, stdout=b'{"status":"ok","result_count":3}', stderr=b"",
            )

        monkeypatch.setattr(mod, "_rodar_probe", _acorda_na_terceira)
        monkeypatch.setattr(mod, "_sono", lambda s: esperas.append(s))

        resultado = mod.analisar_fase2(
            raiz=repo,
            arquivos=["servicos/pagamento.py"],
            sessao=sessao,
        )

        assert resultado["modo_fase2"] == "grafo", "probe com sucesso = modo grafo"
        assert tenta["n"] == 3, "retry com backoff aguardou o cold start"
        assert len(esperas) == 2, "backoff antes da 2a e 3a tentativa"
        esperas_crescentes = esperas == sorted(esperas) and len(set(esperas)) > 1
        assert esperas_crescentes, f"backoff deve crescer: {esperas}"
        dados = json.loads(sessao.read_text(encoding="utf-8"))
        assert dados["fase2"]["modo"] == "grafo"

    def test_probe_exige_sessao_para_registrar_modo(self, tmp_path):
        """Sem sessao (--sessao ausente e nenhuma em docs/diagnosticos/), a CLI falha com exit 1."""
        mod = carregar_fallback()
        repo = tmp_path / "repo_vazio"
        repo.mkdir()
        codigo = mod.main(["analisar", "--repo", str(repo), "--arquivos", "a.py"])
        assert codigo == 1, "sem sessao a CLI deve recusar registrar modo"


class TestAnaliseEstatica:
    """Funcoes internas de Grep/Glob/Read (callers, callees, imports)."""

    def test_buscar_callees_por_leitura_de_corpo(self, tmp_path):
        mod = carregar_fallback()
        repo = tmp_path / "repo"
        repo.mkdir()
        _escrever_projeto(repo)
        callees = mod.buscar_callees(repo, "servicos/pagamento.py", "calcular_total")
        assert any(c["nome"] == "calcular" for c in callees)

    def test_buscar_chamadores_por_nome_de_funcao(self, tmp_path):
        mod = carregar_fallback()
        repo = tmp_path / "repo"
        repo.mkdir()
        _escrever_projeto(repo)
        chamadores = mod.buscar_chamadores(repo, "calcular_total")
        assert any(c["arquivo"] == "app.py" and c["linha"] == 4 for c in chamadores)

    def test_busca_impacto_por_imports(self, tmp_path):
        mod = carregar_fallback()
        repo = tmp_path / "repo"
        repo.mkdir()
        _escrever_projeto(repo)
        importadores = mod.busca_impacto_imports(repo, "servicos/impostos.py")
        assert any(i["arquivo"] == "servicos/pagamento.py" for i in importadores)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])