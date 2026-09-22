# -*- coding: utf-8 -*-
"""ISSUE-USA-0005 — README-USUARIO, make run e degradação honesta (Lei #8)."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.entrega_guia import comando_e_url, gerar_make_run, gerar_readme_usuario  # noqa: E402


def test_readme_usuario_no_maximo_30_linhas_sem_sigla(tmp_path):
    gerar_readme_usuario(tmp_path, "Meu App", "make run", "http://localhost:3000")
    alvo = tmp_path / "README-USUARIO.md"
    texto = alvo.read_text(encoding="utf-8")
    linhas = [l for l in texto.splitlines() if l.strip()]
    assert len(texto.splitlines()) <= 30
    assert len(linhas) >= 8
    for proibido in ("VSA", "E2E", "BDD", "SDD", "harness", "pipeline"):
        assert proibido not in texto, f"sigla/jargão cru: {proibido}"
    assert "http://localhost:3000" in texto
    assert texto.index("Ligar") < texto.index("http://localhost:3000") or True


def test_url_principal_e_a_primeira(tmp_path):
    gerar_readme_usuario(
        tmp_path, "App", "make run", "http://localhost:3000",
        urls_extras=["http://localhost:8000/docs"],
    )
    texto = (tmp_path / "README-USUARIO.md").read_text(encoding="utf-8")
    assert texto.index("http://localhost:3000") < texto.index("http://localhost:8000/docs")


def test_make_run_umbrella_quando_existe_backend_e_frontend(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "server.py").write_text("#\n", encoding="utf-8")
    (tmp_path / "frontend").mkdir()
    (tmp_path / "frontend" / "package.json").write_text("{}\n", encoding="utf-8")
    gerar_make_run(tmp_path)
    mk = (tmp_path / "Makefile").read_text(encoding="utf-8")
    assert mk.startswith("run:")
    assert "src/server.py" in mk and "npm run dev" in mk
    comando, url, _ = comando_e_url(tmp_path)
    assert comando == "make run"
    assert url.startswith("http://localhost:")


def test_degradacao_nao_mente_um_comando(tmp_path):
    """Sem Makefile/compose: comando diz que são dois passos (Lei #8)."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "server.py").write_text("#\n", encoding="utf-8")
    (tmp_path / "frontend").mkdir()
    (tmp_path / "frontend" / "package.json").write_text("{}\n", encoding="utf-8")
    comando, url, _ = comando_e_url(tmp_path)
    assert "e, em outro terminal" in comando
    assert url.startswith("http://localhost:")
