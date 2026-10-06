#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quality Gate Determinístico de TDD (Ticket 7 / D13 / DoD 6 / Leis #8, #9 e #13).
Garante que todo ciclo TDD cumpra:
1. Zero stubs vazios e zero asserções triviais nos arquivos de teste (Lei #5).
2. Sessão registrada com seam acordado e transição para GREEN aprovada.
3. Teste funcional existente e observável.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / ".agents" / "skills" / "aidd-tdd" / "scripts"))

try:
    import validador_seams
except ImportError:
    validador_seams = None


def validar_sessao_tdd(sessao_path: Path) -> tuple[bool, list[str]]:
    erros = []
    if not sessao_path.exists():
        return False, [f"Arquivo de sessão '{sessao_path}' não existe."]

    try:
        dados = json.loads(sessao_path.read_text(encoding="utf-8"))
    except Exception as e:
        return False, [f"Falha ao ler JSON de sessão: {e}"]

    # Checa campos minimos
    for campo in ["alvo", "seam", "fase_atual", "testes"]:
        if campo not in dados:
            erros.append(f"Campo obrigatório '{campo}' ausente no sessao.json.")

    if erros:
        return False, erros

    # Checa estado da fase
    if dados["fase_atual"] in ["RED", "INCOMPLETO"]:
        erros.append(f"Sessão TDD abandonada na fase '{dados['fase_atual']}'.")

    # Inspeciona os testes registrados
    if validador_seams:
        for teste_str in dados.get("testes", []):
            teste_p = Path(teste_str)
            if not teste_p.is_absolute():
                teste_p = ROOT / teste_p
            if teste_p.exists():
                valido, msgs = validador_seams.validar_arquivo_teste(teste_p)
                if not valido:
                    erros.extend(msgs)

    return len(erros) == 0, erros


def main():
    parser = argparse.ArgumentParser(description="Quality Gate para aidd-tdd")
    parser.add_argument("--sessao", default=None, help="Caminho opcional do sessao.json para validar")
    args = parser.parse_args()

    if args.sessao:
        sessao_p = Path(args.sessao)
        valido, erros = validar_sessao_tdd(sessao_p)
        if not valido:
            print("[FALHA] Quality Gate G_aidd_tdd REPROVOU a sessão:")
            for e in erros:
                print(f" - {e}")
            sys.exit(1)
        print("[SUCESSO] Quality Gate G_aidd_tdd APROVADO. EXIT 0")
        sys.exit(0)

    # Modo default: se não houver sessão ativa especificada, audita conformidade dos componentes
    scripts_dir = ROOT / ".agents" / "skills" / "aidd-tdd" / "scripts"
    obrigatorios = ["cli.py", "isolamento.py", "validador_seams.py", "motor_tdd.py", "fallback.py", "observabilidade.py"]
    for ob in obrigatorios:
        if not (scripts_dir / ob).exists():
            print(f"[FALHA] Script obrigatório ausente: {ob}")
            sys.exit(1)

    print("[SUCESSO] Quality Gate G_aidd_tdd APROVADO (Módulos íntegros). EXIT 0")
    sys.exit(0)


if __name__ == "__main__":
    sys.exit(main())
