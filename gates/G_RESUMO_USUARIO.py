#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
G_RESUMO_USUARIO.py — Quality Gate Determinístico (ISSUE-USA-0007 / Lei #1 + #13).

Exige, quando existe raiz de entrega com README-USUARIO.md, também
`RESUMO-USUARIO.md` (≤20 linhas, 3 perguntas) e `RELATORIO-TECNICO.md`.

Exit 0: entrega sem guia ainda (nada a cobrar) OU par completo bem formado.
Exit 1: guia sem resumo / resumo mal formado / relatório ausente.
"""

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent

PERGUNTAS = ("O que mudou", "Como eu abro", "Como eu verifico")
LIMITE_LINHAS = 20


def verificar_raiz(raiz: Path) -> list[str]:
    erros = []
    readme = raiz / "README-USUARIO.md"
    if not readme.is_file():
        return []  # sem entrega ainda — não cobra
    resumo = raiz / "RESUMO-USUARIO.md"
    relatorio = raiz / "RELATORIO-TECNICO.md"
    if not resumo.is_file():
        erros.append(f"{raiz.name}/RESUMO-USUARIO.md ausente após README-USUARIO.md")
        return erros
    texto = resumo.read_text(encoding="utf-8", errors="ignore")
    linhas = texto.splitlines()
    if len(linhas) > LIMITE_LINHAS:
        erros.append(f"RESUMO-USUARIO.md com {len(linhas)} linhas (limite {LIMITE_LINHAS})")
    for p in PERGUNTAS:
        if p.lower() not in texto.lower():
            erros.append(f"RESUMO-USUARIO.md sem a pergunta obrigatória: {p}")
    if not relatorio.is_file():
        erros.append(f"{raiz.name}/RELATORIO-TECNICO.md ausente")
    return erros


def main() -> int:
    # 1) Árvores de entrega reais: docs/planos buckets não são entrega de app.
    #    Cobramos apenas se houver README-USUARIO na raiz do repo (gerado em testes)
    #    + qualquer diretório imediato com README-USUARIO.md.
    erros = verificar_raiz(ROOT)
    for filho in sorted(ROOT.iterdir()) if ROOT.is_dir() else []:
        if filho.is_dir() and filho.name not in {".git", "docs", "gates", "core", "componentes", "scripts", "tools", "tests", "testes"}:
            if (filho / "README-USUARIO.md").is_file():
                erros.extend(verificar_raiz(filho))

    # 2) Gerador presente (contrato do fecho de fluxo)
    gen = ROOT / "core" / "entrega_guia.py"
    if not gen.is_file():
        erros.append("core/entrega_guia.py ausente")
    else:
        t = gen.read_text(encoding="utf-8", errors="ignore")
        if "gerar_resumo_usuario" not in t or "gerar_relatorio_tecnico" not in t:
            erros.append("core/entrega_guia.py sem gerar_resumo_usuario/gerar_relatorio_tecnico")
    orc = ROOT / "scripts" / "orquestrador_sincrono.py"
    if orc.is_file():
        ot = orc.read_text(encoding="utf-8", errors="ignore")
        if "gerar_resumo_usuario" not in ot:
            erros.append("orquestrador_sincrono nao emite RESUMO-USUARIO no fecho")

    if erros:
        print("=" * 70)
        print("VIOLACAO [G_RESUMO_USUARIO]: template duplo de encerramento incompleto!")
        print("Exigido: RESUMO-USUARIO.md (≤20 linhas, 3 perguntas) + RELATORIO-TECNICO.md")
        print("=" * 70)
        for e in erros:
            print(f"- {e}")
        print(f"TOTAL VIOLATIONS: {len(erros)}")
        return 1
    print("[OK] G_RESUMO_USUARIO: template duplo (resumo usuário + relatório técnico) conforme.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
