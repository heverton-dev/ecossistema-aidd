#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — QUALITY GATE: G_HANDOFF_MELHORIA (D15 / Ticket 8)
=============================================================================
Portão de transição melhoria -> plan consumido pelo orquestrador.

Invariantes:
  1. Handoff presente e com JSON válido (ausência = transição reprovada).
  2. Conformidade com componentes/compartilhado/specs/handoff-melhoria.schema.json.
  3. Assinatura (sha256 canônico ou hmac-sha256 com AIDD_HANDOFF_CHAVE) confere.
  4. Artefatos listados existem e mantêm o sha256 registrado.
  5. Só status SUCESSO com codigo_saida 0 libera a próxima fase.

Saída binária (Lei #2): exit 0 = transição liberada; exit 1 = bloqueada.

Uso:
  python gates/G_HANDOFF_MELHORIA.py [--handoff handoff-melhoria.json] [--repo-root .]
=============================================================================
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT_DIR = Path(__file__).resolve().parent.parent
SKILL_SCRIPTS = ROOT_DIR / ".agents" / "skills" / "aidd-melhoria" / "scripts"
if str(SKILL_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SKILL_SCRIPTS))

import handoff  # noqa: E402


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Gate de transição melhoria -> plan via handoff-melhoria.json")
    parser.add_argument("--handoff", default=str(ROOT_DIR / "handoff-melhoria.json"))
    parser.add_argument("--repo-root", default=None, help="Base dos caminhos relativos dos artefatos")
    args = parser.parse_args(argv)

    resultado = handoff.transicionar_fase(Path(args.handoff), repo_root=args.repo_root)
    if resultado["liberada"]:
        print(f"[G_HANDOFF_MELHORIA] OK: transição liberada para '{resultado['proxima_fase']}' "
              "(requer aprovação humana).")
        return 0
    print("[G_HANDOFF_MELHORIA] REPROVADO: transição bloqueada.")
    for erro in resultado["erros"]:
        print(f"  - {erro}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
