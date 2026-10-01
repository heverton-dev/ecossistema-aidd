#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PIPELINE PREFECT — SHIM DE COMPATIBILIDADE (DEPRECADO)
=======================================================
A partir do Item 2 (unificar-orquestradores-generator-e-ops), a orquestração
genérica do pipeline de 8 fases via Prefect vive em UM ÚNICO orquestrador
canônico:

    scripts/pipeline_completo.py

Este módulo NÃO contém mais lógica própria de orquestração — é apenas um
shim fino de compatibilidade que reexporta os símbolos públicos do módulo
canônico para não quebrar imports históricos e a suíte de testes que
referencia o nome antigo (`import pipeline_prefect as pp`).

`_PREFECT_HOME` é recalculado aqui a cada import/reload (via
`pipeline_completo.resolver_prefect_home`) para refletir o valor atual de
AIDD_PREFECT_HOME sem duplicar a lógica de resolução. Nova execução deve
usar o orquestrador canônico:

    python scripts/pipeline_completo.py "ideia" --pasta ../PROJ --orquestrador prefect
"""

import os

from pipeline_completo import (
    _cache_por_fase,
    _chave_checkpoint,
    _PREFECT_IMPORT_ERRO,
    _PREFECT_IMPORT_OK,
    _RETRIES,
    _task_fase_1,
    _task_fase_2,
    _task_fase_3,
    _task_fase_4,
    _task_fase_5,
    _task_fase_6,
    _task_fase_7,
    _task_fase_8,
    disponibilidade_prefect,
    executar_pipeline_prefect,
    resolver_prefect_home,
)

# Recalculado no import/reload do shim: preserva a semântica de
# AIDD_PREFECT_HOME (monkeypatch + reload) sem duplicar a resolução.
_PREFECT_HOME = resolver_prefect_home()

# Ajusta o PREFECT_HOME efetivo do processo para o valor recém-resolvido,
# mantendo o comportamento do antigo módulo standalone.
os.environ['PREFECT_HOME'] = _PREFECT_HOME


if __name__ == '__main__':
    import argparse
    import json as _json
    import sys as _sys

    parser = argparse.ArgumentParser(description='Executa pipeline via Prefect (via orquestrador canônico)')
    parser.add_argument('ideia', help='Ideia do projeto')
    parser.add_argument('--pasta', required=True)
    parser.add_argument('--interativo', action='store_true')
    parser.add_argument('--implementar-codigo', action='store_true')
    args = parser.parse_args()
    ok, msg = disponibilidade_prefect()
    if not ok:
        _sys.exit(f'❌ {msg}')
    res = executar_pipeline_prefect(
        args.ideia, args.pasta,
        nao_interativo=not args.interativo,
        implementar_codigo=args.implementar_codigo,
    )
    print(_json.dumps(res, indent=2, ensure_ascii=False, default=str))
    _sys.exit(0 if res.get('status') == 'COMPLETO' else 1)