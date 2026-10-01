#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quality Gate Determinístico de Especificação Técnica (Ticket 7 / D13 / DoD 6 / Leis #8, #9 e #13).
Garante que todo documento de especificação cumpra:
1. As 5 seções canônicas obrigatórias (Contexto, Contratos, Invariantes, Critérios Binários, Modos de Falha).
2. Critérios de aceitação verificáveis mecanicamente (exit codes, status codes HTTP, asserts, etc.).
3. Invariantes e regras de negócio numeradas.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Tenta carregar do componentes compartilhado ou do .agents
caminhos_busca = [
    ROOT / "componentes" / "compartilhado" / "skills" / "aidd-spec" / "scripts",
    ROOT / ".agents" / "skills" / "aidd-spec" / "scripts"
]
for c in caminhos_busca:
    if c.exists() and str(c) not in sys.path:
        sys.path.insert(0, str(c))

try:
    import parser as spec_parser
    import motor as spec_motor
except ImportError:
    spec_parser = None
    spec_motor = None


def validar_spec_conteudo(texto: str) -> tuple[bool, list[str]]:
    erros = []
    if not spec_parser or not spec_motor:
        return False, ["Módulos de parsing ou validação de aidd-spec indisponíveis."]

    secoes, erros_parse = spec_parser.parsear_especificacao_markdown(texto)
    if erros_parse:
        erros.extend(erros_parse)
        return False, erros

    resumo, erros_motor = spec_motor.validar_regras_especificacao(secoes)
    if erros_motor:
        erros.extend(erros_motor)

    return len(erros) == 0, erros


def main():
    parser = argparse.ArgumentParser(description="Quality Gate para aidd-spec")
    parser.add_argument("--arquivo", default=None, help="Caminho opcional do arquivo markdown com especificação")
    args = parser.parse_args()

    if args.arquivo:
        p = Path(args.arquivo)
        if not p.exists():
            print(f"[FALHA] Arquivo '{args.arquivo}' não existe.")
            sys.exit(1)
        texto = p.read_text(encoding="utf-8")
        valido, erros = validar_spec_conteudo(texto)
        if not valido:
            print("[FALHA] Quality Gate G_aidd_spec REPROVOU a especificação:")
            for e in erros:
                print(f" - {e}")
            sys.exit(1)
        print("[SUCESSO] Quality Gate G_aidd_spec APROVADO. EXIT 0")
        sys.exit(0)

    # Modo default: valida scripts obrigatórios
    scripts_dir = ROOT / "componentes" / "compartilhado" / "skills" / "aidd-spec" / "scripts"
    obrigatorios = ["cli.py", "isolamento.py", "parser.py", "motor.py", "fallback.py", "observabilidade.py", "rollback.py", "handoff.py"]
    for ob in obrigatorios:
        if not (scripts_dir / ob).exists():
            print(f"[FALHA] Script obrigatório ausente em aidd-spec: {ob}")
            sys.exit(1)

    print("[SUCESSO] Quality Gate G_aidd_spec APROVADO (Módulos íntegros). EXIT 0")
    sys.exit(0)


if __name__ == "__main__":
    sys.exit(main())
