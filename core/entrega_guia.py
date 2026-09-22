# -*- coding: utf-8 -*-
"""Guia do usuário e comando único de subida (ISSUE-USA-0005)."""

from pathlib import Path


def gerar_readme_usuario(
    raiz: Path,
    nome_app: str,
    comando_subir: str,
    url_principal: str,
    urls_extras: list[str] | None = None,
) -> Path:
    """Escreve README-USUARIO.md (≤30 linhas, PT-BR simples, zero sigla)."""
    extras = urls_extras or []
    linhas = [
        f"# {nome_app} — como usar",
        "",
        "## 1. Instalar (uma vez só)",
        "No terminal, dentro desta pasta:",
        "  python -m venv .venv",
        "  .venv\\Scripts\\activate   (no Linux/Mac: source .venv/bin/activate)",
        "  pip install -r requirements.txt",
        "  cd frontend && npm install && cd ..",
        "",
        "## 2. Ligar tudo",
        f"  {comando_subir}",
        "",
        "## 3. Abrir no navegador",
        f"  {url_principal}",
        "",
    ]
    if extras:
        linhas += ["## 4. Outras telas (só se precisar)"]
        linhas += [f"  {u}" for u in extras]
        linhas.append("")
    else:
        linhas += ["## 4. Outras telas", "  Não há — tudo fica no endereço acima.", ""]

    alvo = raiz / "README-USUARIO.md"
    alvo.write_text("\n".join(linhas[:30]), encoding="utf-8")
    return alvo


def gerar_make_run(raiz: Path) -> Path:
    """Escreve Makefile com o comando único `make run` (umbrella).

    Sobe backend + frontend juntos quando existirem; senão, explica o passo.
    """
    tem_server = (raiz / "src" / "server.py").is_file()
    tem_frontend = (raiz / "frontend" / "package.json").is_file()
    tem_compose = (raiz / "docker-compose.yml").is_file()

    if tem_compose:
        corpo = (
            "run:\n"
            "\tdocker compose up\n"
        )
        comando = "make run"
    elif tem_server and tem_frontend:
        corpo = (
            "run:\n"
            "\tpython src/server.py &\n"
            "\tcd frontend && npm run dev\n"
        )
        comando = "make run"
    elif tem_server:
        corpo = "run:\n\tpython src/server.py\n"
        comando = "make run"
    else:
        corpo = "run:\n\t@echo Veja README-USUARIO.md — nada para subir ainda.\n"
        comando = "make run"

    alvo = raiz / "Makefile"
    alvo.write_text(corpo, encoding="utf-8")
    return alvo


def comando_e_url(raiz: Path) -> tuple[str, str, list[str]]:
    """Decide comando de subida e URL principal. Nunca mente '1 comando' (Lei #8)."""
    tem_compose = (raiz / "docker-compose.yml").is_file()
    tem_server = (raiz / "src" / "server.py").is_file()
    tem_frontend = (raiz / "frontend" / "package.json").is_file()
    tem_make = (raiz / "Makefile").is_file()

    if tem_compose or tem_make:
        if tem_compose and not tem_make:
            comando = "docker compose up"
        else:
            comando = "make run"
        url = "http://localhost:3000"
        extras = ["http://localhost:8000/docs  (guia técnico do motor)"]
        return comando, url, extras

    if tem_server and tem_frontend:
        # Degradação honesta: são dois comandos.
        comando = "python src/server.py   e, em outro terminal:  cd frontend && npm run dev"
        url = "http://localhost:3000"
        return comando, url, []

    if tem_server:
        comando = "python src/server.py"
        return comando, "http://localhost:8000/docs", []

    return "(veja o passo 2 do guia)", "(veja o guia)", []
