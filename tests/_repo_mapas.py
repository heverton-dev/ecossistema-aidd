# -*- coding: utf-8 -*-
"""
Repositório de teste dos mapas visuais (aidd-visual-maps ciclo-01).

Copia para uma pasta temporária só o que o catálogo de peças, os mapas e o livro
leem (árvore de trabalho atual, versionados e novos ainda não versionados), para
os testes rodarem os scripts de verdade, por subprocesso, sem tocar no repositório real.
Não é teste (o nome não começa com test_): é a fixture compartilhada.
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# O que os coletores de scripts/catalogo_pecas.py leem; as pastas de harness ficam
# de fora (o catálogo da cópia fica coerente consigo mesmo, só com menos skills em disco).
FONTES = ("scripts", "modulos", "componentes", "core", "contratos", "tests", "docs/mapas-visuais",
          "docs/auditoria", "docs/livros/mapas-aidd", "docs/planos", "docs/melhorias", "AGENTS.md",
          "ecossistema.py", ".pre-commit-config.yaml", ".githooks", ".mcp.json", "opencode.jsonc",
          "mimocode.jsonc", ".claude/settings.json", ".claude/hooks")


def copiar_repo(destino: Path) -> Path:
    """Copia as FONTES da árvore de trabalho para `destino` e inicia um git vazio nela."""
    lista = subprocess.run(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard", "--", *FONTES],
                           cwd=ROOT, capture_output=True, check=True).stdout.decode("utf-8").split("\0")
    for rel in filter(None, lista):
        origem = ROOT / rel
        if not origem.is_file():  # versionado mas apagado na árvore de trabalho
            continue
        alvo = destino / rel
        alvo.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(origem, alvo)
    subprocess.run(["git", "init", "-q"], cwd=destino, check=True)
    return destino


def commitar(raiz: Path, *caminhos: str, mensagem: str = "fixture") -> None:
    """Commit local na cópia (autor fixo, sem hooks): o estado 'versionado' da fixture."""
    subprocess.run(["git", "add", "--", *caminhos], cwd=raiz, check=True)
    subprocess.run(["git", "-c", "user.name=fixture", "-c", "user.email=fixture@local", "-c", "core.hooksPath=/dev/null",
                    "commit", "-q", "-m", mensagem], cwd=raiz, check=True)


def rodar(raiz: Path, *args: str, env: dict | None = None) -> subprocess.CompletedProcess:
    """Roda `python <args>` dentro da cópia e devolve o processo (exit code real, sem pipe)."""
    ambiente = {**os.environ, "PYTHONIOENCODING": "utf-8", **(env or {})}
    return subprocess.run([sys.executable, *args], cwd=raiz, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", env=ambiente, timeout=600)


CLI_VMAPS = "componentes/compartilhado/skills/aidd-visual-maps/scripts/cli.py"


def obter_repo_base_gerado(tmp_path_factory) -> Path:
    """Gera um repositório base completo uma única vez para ser copiado rapidamente."""
    base = tmp_path_factory.mktemp("repo_mapas_gerado_base") / "repo"
    copiar_repo(base)
    commitar(base, ".", mensagem="fixture base")
    proc = rodar(base, CLI_VMAPS, "gerar", env={"AIDD_MEDICOES_DIR": str(base.parent / "medicoes")})
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return base

