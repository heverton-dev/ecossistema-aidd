#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quality Gate Determinístico de Entrevista Socrática (Ticket 7 / D13 / DoD 6 / Leis #8, #9 e #13).
Garante que toda rodada socrática cumpra:
1. Perguntas numeradas (1, 2, 3...).
2. Resposta recomendada por pergunta acompanhada de justificativa técnica causal (porque, pois, etc.).
3. Separação de fatos do repositório versus decisões do usuário.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

caminhos_busca = [
    ROOT / "componentes" / "compartilhado" / "skills" / "aidd-grill" / "scripts",
    ROOT / ".agents" / "skills" / "aidd-grill" / "scripts"
]
for c in caminhos_busca:
    if c.exists() and str(c) not in sys.path:
        sys.path.insert(0, str(c))

try:
    import parser as grill_parser
    import motor as grill_motor
except ImportError:
    grill_parser = None
    grill_motor = None


def validar_grill_conteudo(texto: str) -> tuple[bool, list[str]]:
    erros = []
    if not grill_parser or not grill_motor:
        return False, ["Módulos de parsing ou validação de aidd-grill indisponíveis."]

    perguntas, erros_parse = grill_parser.parsear_rodada_socratica(texto)
    if erros_parse:
        erros.extend(erros_parse)
        return False, erros

    resumo, erros_motor = grill_motor.validar_perguntas_socromaticas(perguntas)
    if erros_motor:
        erros.extend(erros_motor)

    return len(erros) == 0, erros


def main():
    parser = argparse.ArgumentParser(description="Quality Gate para aidd-grill")
    parser.add_argument("--arquivo", default=None, help="Caminho opcional do arquivo markdown com a rodada socrática")
    args = parser.parse_args()

    if args.arquivo:
        p = Path(args.arquivo)
        if not p.exists():
            print(f"[FALHA] Arquivo '{args.arquivo}' não existe.")
            sys.exit(1)
        texto = p.read_text(encoding="utf-8")
        valido, erros = validar_grill_conteudo(texto)
        if not valido:
            print("[FALHA] Quality Gate G_aidd_grill REPROVOU a rodada socrática:")
            for e in erros:
                print(f" - {e}")
            sys.exit(1)
        print("[SUCESSO] Quality Gate G_aidd_grill APROVADO. EXIT 0")
        sys.exit(0)

    # Modo default: valida scripts obrigatórios
    scripts_dir = ROOT / "componentes" / "compartilhado" / "skills" / "aidd-grill" / "scripts"
    obrigatorios = ["cli.py", "isolamento.py", "parser.py", "motor.py", "fallback.py", "observabilidade.py", "rollback.py", "handoff.py"]
    for ob in obrigatorios:
        if not (scripts_dir / ob).exists():
            print(f"[FALHA] Script obrigatório ausente em aidd-grill: {ob}")
            sys.exit(1)

    print("[SUCESSO] Quality Gate G_aidd_grill APROVADO (Módulos íntegros). EXIT 0")
    sys.exit(0)


if __name__ == "__main__":
    sys.exit(main())
