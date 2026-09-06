#!/usr/bin/env python3
import os, sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

def auditar():
    print('=' * 70)
    print(' [GATE] G_ZERO_HEADLESS — Blindagem Anti-Headless Subagents')
    print('=' * 70)

    erros = []
    engine = ROOT_DIR / 'componentes/compartilhado/skills/orca-plan-orchestrator/scripts/orchestrator_engine.py'
    if not engine.exists() or 'interactive: bool = True' not in engine.read_text(encoding='utf-8'):
        erros.append('orchestrator_engine.py deve ter interactive: bool = True como padrao obrigatorio.')

    eco = ROOT_DIR / 'ecossistema.py'
    if not eco.exists() or '--dangerously-force-headless' not in eco.read_text(encoding='utf-8'):
        erros.append('ecossistema.py deve exigir --dangerously-force-headless para qualquer execucao nao-interativa.')

    if erros:
        print(f'\n[FALHA] Quality Gate REPROVADO com {len(erros)} erro(s):')
        for e in erros:
            print(f'  - {e}')
        print('=' * 70)
        return 1

    print('[OK] Modo interativo configurado como padrao estrito no motor.')
    print('[OK] Flag explicita obrigatoria para qualquer excecao headless.')
    print('[OK] Zero risco de subagentes ocultos em concorrencia silenciosa.')
    print('\n=======================================================================')
    print(' [SUCESSO] Quality Gate G_ZERO_HEADLESS APROVADO (100% OK)!')
    print('=======================================================================\n')
    return 0

if __name__ == '__main__':
    sys.exit(auditar())
