# -*- coding: utf-8 -*-
"""
Testes do Ticket 3 (D8 / DoD 3) — Detecção de Grafo Desatualizado.

Exige o entregável .agents/skills/aidd-diagnose/scripts/cobertura_grafo.py:
- Antes da Fase 2, cada arquivo suspeito é consultado com
  query_graph_tool(pattern="file_summary", target=<arquivo>).
- 0 resultados = grafo desatualizado → update único do grafo → reconsulta.
- Continua 0 = modo Fase 2 "fallback" (handoff Ticket 4).
- Arquivo versionado SEM nós no grafo NUNCA sai como "0 impactados".
- medir: contagem de .py versionados sem nó em .code-review-graph/graph.db
  antes / após update / após build, com causa-raiz em docs/diagnosticos/.
"""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
SCRIPT = ROOT_DIR / ".agents" / "skills" / "aidd-diagnose" / "scripts" / "cobertura_grafo.py"


def carregar_cobertura():
    """Importa cobertura_grafo.py do entregável."""
    spec = importlib.util.spec_from_file_location("aidd_diagnose_cobertura_grafo", str(SCRIPT))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-c", "user.email=t@test", "-c", "user.name=t", *args],
        cwd=str(repo), capture_output=True, text=True,
    )


def _repo_suspeito(tmp_path: Path) -> Path:
    """Repo git de teste: modulo.py (parseável, alterado no último commit),
    vazio.py (sem definições) e binario.py (nunca indexado pelo parser)."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", ".")
    _git(repo, "commit", "-q", "--allow-empty", "-m", "init")
    (repo / "modulo.py").write_text("def funcao():\n    return 1\n", encoding="utf-8")
    (repo / "vazio.py").write_text("", encoding="utf-8")
    (repo / "binario.py").write_bytes(b"a\x00b")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "add")
    (repo / "modulo.py").write_text("def funcao():\n    return 2\n", encoding="utf-8")
    (repo / "vazio.py").write_text("", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "change")
    return repo


def _rodar(args: list) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )


class TestEntregavel:
    """O módulo cobertura_grafo.py existe e expõe a API de Fase 2."""

    def test_modulo_importa_e_expe_api(self):
        mod = carregar_cobertura()
        assert hasattr(mod, "verificar_cobertura"), "verificar_cobertura ausente"
        assert hasattr(mod, "medir_cobertura"), "medir_cobertura ausente"
        assert callable(mod.main), "main ausente"

    def test_cli_verificar_responde(self, tmp_path):
        repo = _repo_suspeito(tmp_path)
        r = _rodar(["verificar", "--repo", str(repo), "modulo.py"])
        assert r.returncode in (0, 2), f"exit inesperado: {r.returncode} {r.stderr}"
        json.loads(r.stdout)


class TestNuncaZeroImpactoSemNos:
    """Regra central D8: arquivo sem nós no grafo nunca sai como '0 impactados'."""

    def test_arquivo_sem_nos_vai_para_fallback_e_nao_zero_impacto(self, tmp_path):
        repo = _repo_suspeito(tmp_path)
        r = _rodar(["verificar", "--repo", str(repo), "binario.py"])
        dados = json.loads(r.stdout)

        assert r.returncode == 2, f"fallback deveria dar exit 2, veio {r.returncode}"
        assert dados["modo_fase2"] == "fallback"
        assert dados["handoff"] == "ticket_4_fallback"
        assert dados["pode_reportar_zero_impacto"] is False

        arq = dados["arquivos"]["binario.py"]
        assert arq["coberto"] is False
        assert arq["estado"] == "fallback"
        assert arq["nos_no_arquivo"] is None, "nó 0 vazado como número = falso '0 impactados'"
        assert arq["zero_impacto_permitido"] is False
        assert arq["aviso"] == "grafo_desatualizado"

        # Nenhum arquivo sem cobertura pode aparecer com contagem numérica 0.
        for nome, item in dados["arquivos"].items():
            if not item["coberto"]:
                assert item["nos_no_arquivo"] is None, f"{nome} reportou nó numérico sem cobertura"

    def test_update_executado_uma_vez_para_todos_suspeitos(self, tmp_path):
        repo = _repo_suspeito(tmp_path)
        r = _rodar([
            "verificar", "--repo", str(repo),
            "binario.py", "vazio.py", "modulo.py",
        ])
        dados = json.loads(r.stdout)
        assert dados["atualizacoes_executadas"] == 1, "update deve rodar exatamente 1 vez"
        # modulo.py é alterado desde HEAD~1 e parseável → coberto após update.
        assert dados["arquivos"]["modulo.py"]["coberto"] is True
        assert dados["arquivos"]["modulo.py"]["nos_no_arquivo"] >= 1
        assert dados["arquivos"]["binario.py"]["coberto"] is False


class TestArquivoCobertoModoGrafo:
    """Caminho feliz: cobertura confirmada → Fase 2 em modo grafo."""

    def test_arquivo_coberto_sai_exit_0_modo_grafo(self, tmp_path):
        repo = _repo_suspeito(tmp_path)
        r = _rodar(["verificar", "--repo", str(repo), "modulo.py"])
        dados = json.loads(r.stdout)

        assert r.returncode == 0, f"esperado exit 0, veio {r.returncode}: {r.stderr}"
        assert dados["modo_fase2"] == "grafo"
        assert dados["handoff"] is None
        assert dados["pode_reportar_zero_impacto"] is True

        arq = dados["arquivos"]["modulo.py"]
        assert arq["coberto"] is True
        assert arq["estado"] in ("coberto", "coberto_apos_atualizacao")
        assert arq["nos_no_arquivo"] >= 1
        assert arq["zero_impacto_permitido"] is True


class TestMedicaoCobertura:
    """Medição de .py versionados sem nó antes / após update / após build."""

    def test_medir_conta_faltantes_antes_update_build(self, tmp_path):
        repo = _repo_suspeito(tmp_path)
        r = _rodar([
            "medir", "--repo", str(repo),
            "--etapas", "antes,update,build", "--salvar",
        ])
        dados = json.loads(r.stdout)

        assert r.returncode == 0, f"medir falhou: {r.stderr}"
        assert dados["py_versionados"] == 3

        etapas = {e["etapa"]: e for e in dados["etapas"]}
        assert etapas["antes"]["cobertos"] == 0
        assert etapas["antes"]["faltantes"] == 3
        # update cobre apenas o arquivo alterado desde HEAD~1 (modulo.py).
        assert etapas["update"]["cobertos"] == 1
        assert etapas["update"]["faltantes"] == 2
        # build completo indexa também vazio.py; binario.py é pulo do parser.
        assert etapas["build"]["cobertos"] == 2
        assert etapas["build"]["faltantes"] == 1

        assert dados["raiz_causa"], "causa-raiz obrigatória"
        assert isinstance(dados["raiz_causa"], str) and len(dados["raiz_causa"]) > 20

        sessao = Path(dados["sessao_dir"])
        assert (sessao / "medicao-cobertura-grafo.json").is_file()
        relatorio = sessao / "RELATORIO-COBERTURA-GRAFO.md"
        assert relatorio.is_file()
        texto = relatorio.read_text(encoding="utf-8")
        assert "raiz" in texto.lower() or "causa" in texto.lower()
        assert "faltantes" in texto.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
