# -*- coding: utf-8 -*-
"""
CLI Oficial do aidd-planner
Uso:
  python -m aidd_planner.cli init --fluxo <1|2|3> --nome <nome> --pasta <destino>
  python -m aidd_planner.cli validate <caminho_plano.json>
  python -m aidd_planner.cli export <caminho_plano.json> --formato factory --saida <arquivo>
  python -m aidd_planner.cli mobbin <search|status> [args]
  python -m aidd_planner.cli audit [pasta]
"""

import sys
from src.cli import main

if __name__ == "__main__":
    sys.exit(main())
