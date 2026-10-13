"""Ticket 3 (ETAPA_03): 'pure --dry-run' nao pode criar a pasta do projeto.

Roda o comando real por subprocess (mesmo mecanismo do usuario), sem importar o
orquestrador: assim o teste nao altera o catalogo factual de pecas.
"""
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def test_pure_dry_run_nao_cria_pasta_do_projeto(tmp_path):
    pasta = tmp_path / "projetos" / "teste-dry"
    res = subprocess.run(
        [sys.executable, "ecossistema.py", "pure", "--nome", "Teste Dry", "--slug", "teste-dry",
         "--dominio", "gestao", "--pasta", str(pasta), "--dry-run"],
        cwd=RAIZ, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300,
    )
    assert res.returncode == 0, res.stdout[-800:] + res.stderr[-800:]
    assert not pasta.exists()
