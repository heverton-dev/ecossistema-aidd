#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GATE: G_SESSAO_HERMETICA — Item 4 [TK-6] hermeticidade verificável de sessões.

Auditoria AST (zero token, determinística) sobre os executores headless do
aidd-generator:

1. Todo processo CLI de harness externo disparado via subprocess (lista argv
   literal contendo binário de harness conhecido) deve carregar flag de sessão
   efêmera/isolada conhecida (FLAGS_SESSAO_EFEMERA_POR_HARNESS) OU passar por
   validar_sessao_hermetica/forcar_sessao_hermetica.
2. Verifica que FLAGS_SESSAO_EFEMERA_POR_HARNESS existe em utils_delegacao.py
   e que rotular_tipo_sessao é usado nos dois modos (delegado e headless).

Nota de escopo honesto (Regra #9): este gate audita ESTRUTURA (AST) dos
executores do próprio repositório. Não intercepta runtime de harnesses
externos — igual ao G_ZERO_HEADLESS do ecossistema (lint estrutural).
Comandos git/pytest/python de teste não são executores de LLM e não exigem
flag de sessão.

Uso:
    python scripts/gates/G_SESSAO_HERMETICA.py
Exit: 0 = aprovado, 1 = violação encontrada.
"""

import ast
import sys
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

RAIZ = Path(__file__).resolve().parent.parent  # .../aidd-generator/scripts
PHASES_DIR = RAIZ / 'phases'

# Binários de harness CLI cujas invocações exigem flag de sessão efêmera.
BINARIOS_HARNESS = {
    'claude', 'codex', 'agy', 'opencode', 'mimo', 'gemini', 'hermes', 'freebuff',
}

FLAGS_EFEMERAS_CONHECIDAS = {
    '--no-session-persistence', '--ephemeral', '--ephemeral-session',
    '--no-persist', '--continue-session=false', '--sessionless',
}


def _caminho_chamada(call: ast.Call) -> str:
    """Nome textual da função chamada (ex.: 'subprocess.run')."""
    func = call.func
    if isinstance(func, ast.Attribute):
        base = func.value
        if isinstance(base, ast.Name):
            return f'{base.id}.{func.attr}'
        return func.attr
    if isinstance(func, ast.Name):
        return func.id
    return ''


def _argv_da_chamada(call: ast.Call):
    """Extrai o primeiro argumento se for lista/tupla literal de strings."""
    if not call.args:
        return None
    primeiro = call.args[0]
    if isinstance(primeiro, (ast.List, ast.Tuple)):
        elementos = []
        for el in primeiro.elts:
            if isinstance(el, ast.Constant) and isinstance(el.value, str):
                elementos.append(el.value)
            else:
                return None  # argv dinâmico: não auditável estaticamente
        return elementos
    return None


def _funcoes_guarda(arvore: ast.AST) -> set:
    """Nomes de funções que validam hermeticidade (definidas ou importadas)."""
    guarda = {'validar_sessao_hermetica', 'forcar_sessao_hermetica'}
    for no in ast.walk(arvore):
        if isinstance(no, ast.ImportFrom) and no.module and 'utils_delegacao' in no.module:
            for alias in no.names:
                if alias.name in ('validar_sessao_hermetica', 'forcar_sessao_hermetica'):
                    guarda.add(alias.asname or alias.name)
        elif isinstance(no, ast.FunctionDef):
            corpo_fonte = ast.dump(no)
            if 'validar_sessao_hermetica' in corpo_fonte or 'forcar_sessao_hermetica' in corpo_fonte:
                guarda.add(no.name)
    return guarda


def auditar_arquivo(caminho: Path):
    """Retorna lista de violações (argv literal de harness sem flag efêmera)."""
    violacoes = []
    try:
        fonte = caminho.read_text(encoding='utf-8')
    except (OSError, UnicodeDecodeError):
        return violacoes
    try:
        arvore = ast.parse(fonte)
    except SyntaxError:
        return violacoes

    guardas = _funcoes_guarda(arvore)

    class Visitante(ast.NodeVisitor):
        def __init__(self):
            self.funcoes_com_guarda = set()

        def visit_Call(self, no: ast.Call):
            nome_chamada = _caminho_chamada(no)
            if nome_chamada in ('subprocess.run', 'subprocess.Popen',
                                'subprocess.call', 'subprocess.check_output',
                                'run', 'Popen', 'check_output'):
                argv = _argv_da_chamada(no)
                if argv:
                    binario = Path(argv[0]).name.lower()
                    if binario in BINARIOS_HARNESS:
                        tem_flag = any(a in FLAGS_EFEMERAS_CONHECIDAS for a in argv)
                        usa_guarda = nome_chamada.split('.')[-1] in (
                            'validar_sessao_hermetica', 'forcar_sessao_hermetica'
                        )
                        if not tem_flag:
                            violacoes.append(
                                (caminho.name, no.lineno, binario, argv[:4])
                            )
            self.generic_visit(no)

    Visitante().visit(arvore)
    return violacoes


def auditar_rotulagem_telemetria():
    """Verifica que rotular_tipo_sessao existe e é aplicada nos dois modos."""
    problemas = []
    arquivo = PHASES_DIR / 'utils_delegacao.py'
    if not arquivo.exists():
        return [f'{arquivo} não encontrado']
    try:
        arvore = ast.parse(arquivo.read_text(encoding='utf-8'))
    except SyntaxError as e:
        return [f'utils_delegacao.py com SyntaxError: {e}']

    nomes_def = {n.name for n in ast.walk(arvore) if isinstance(n, ast.FunctionDef)}
    if 'rotular_tipo_sessao' not in nomes_def:
        problemas.append('rotular_tipo_sessao ausente em utils_delegacao.py')
    if 'FLAGS_SESSAO_EFEMERA_POR_HARNESS' not in arquivo.read_text(encoding='utf-8'):
        problemas.append('FLAGS_SESSAO_EFEMERA_POR_HARNESS ausente')

    fonte = arquivo.read_text(encoding='utf-8')
    if "rotular_tipo_sessao('delegado')" not in fonte:
        problemas.append("modo delegado não rotula tipo_sessao")
    if "rotular_tipo_sessao('headless')" not in fonte:
        problemas.append("modo headless não rotula tipo_sessao")
    return problemas


def main() -> int:
    print('🔒 G_SESSAO_HERMETICA — hermeticidade de sessões headless [TK-6]')
    alvo = [PHASES_DIR / 'utils_delegacao.py', PHASES_DIR / 'utils_subagente_ephemero.py',
            PHASES_DIR / 'utils_fleet_discovery.py']
    alvo = [a for a in alvo if a.exists()]

    violacoes_totais = []
    for arquivo in alvo:
        violacoes_totais.extend(auditar_arquivo(arquivo))

    problemas_rotulagem = auditar_rotulagem_telemetria()

    if violacoes_totais:
        print(f'✗ {len(violacoes_totais)} invocação(ões) de harness sem flag de sessão efêmera:')
        for nome_arquivo, linha, binario, argv in violacoes_totais:
            print(f'   {nome_arquivo}:{linha} — binário "{binario}" argv={argv}')
    else:
        print('✓ Nenhuma invocação de harness CLI sem flag de sessão efêmera')

    if problemas_rotulagem:
        print('✗ Rotulagem de tipo de sessão incompleta:')
        for p in problemas_rotulagem:
            print(f'   - {p}')
    else:
        print('✓ Telemetria rotulada nos dois modos (sessao_isolada / sessao_compartilhada_delegada)')

    if violacoes_totais or problemas_rotulagem:
        print('\n✗ GATE FALHOU')
        return 1
    print('\n✅ GATE APROVADO')
    return 0


if __name__ == '__main__':
    sys.exit(main())
