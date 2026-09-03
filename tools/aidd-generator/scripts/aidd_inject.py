#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI: aidd_inject — Injetor Universal de Componentes
aidd-generator

Materializa Skills, MCPs, Rules, Specs e Configs neste projeto de forma
transacional, com sincronização automática de anchors globais (AGENTS.md,
HARNESS-COMPAT.json, PLANO-EXECUCAO-ESTRUTURADO.json).

Uso:
    python scripts/aidd_inject.py inject skill "auditoria-seguranca" --descricao "..."
    python scripts/aidd_inject.py inject mcp "verificador-cve" --descricao "..." --forcar
    python scripts/aidd_inject.py "crie uma skill de auditoria de dependências"
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

_PHASES_DIR = _ROOT / 'scripts' / 'phases'
if str(_PHASES_DIR) not in sys.path:
    sys.path.insert(0, str(_PHASES_DIR))

from scripts.core.injector.injetor import injetar, ResultadoInjecao
from scripts.core.injector.profiles_registry import PROJETOS_SUPORTADOS
from utils_intent_router import detectar_injecao, slug_a_partir_da_ideia


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog='aidd_inject.py',
        description='Injetor Universal de Componentes (skills, MCPs, rules, specs, configs)',
    )
    sub = parser.add_subparsers(dest='comando')

    p_inject = sub.add_parser('inject', help='Injeta um componente explicitamente')
    p_inject.add_argument('tipo', choices=['skill', 'mcp', 'rule', 'spec', 'config'])
    p_inject.add_argument('nome', help='Slug do componente (kebab-case)')
    p_inject.add_argument('--descricao', required=True, help='Descrição em linguagem natural')
    p_inject.add_argument('--alvo-projeto', default='aidd-generator', choices=list(PROJETOS_SUPORTADOS))
    p_inject.add_argument('--forcar', action='store_true', help='Sobrescreve destinos já existentes')
    p_inject.add_argument('--root', default=None, help='Raiz do projeto (default: diretório atual)')

    return parser


def _relatar(resultado: ResultadoInjecao) -> int:
    if resultado.sucesso:
        print(f"✅ Componente injetado: {resultado.tipo} '{resultado.nome}'")
        print(f"   Destino principal: {resultado.dest}")
        if resultado.arquivos_publicados:
            print(f"   Arquivos publicados: {', '.join(resultado.arquivos_publicados)}")
        if resultado.anchors_atualizados:
            print(f"   Anchors sincronizados: {', '.join(resultado.anchors_atualizados)}")
        return 0

    print("❌ Falha ao injetar componente")
    if resultado.erro:
        print(f"   Erro: {resultado.erro}")
    for erro in resultado.erros:
        print(f"   - {erro}")
    return 1


def _cmd_inject(args: argparse.Namespace) -> int:
    root = Path(args.root) if args.root else None
    resultado = injetar(
        nome=args.nome,
        descricao=args.descricao,
        tipo=args.tipo,
        alvo_projeto=args.alvo_projeto,
        root=root,
        force=args.forcar,
    )
    return _relatar(resultado)


def _extrair_flag(argv: List[str], nome_flag: str) -> 'tuple[Optional[str], List[str]]':
    """Remove '--flag valor' de uma lista de argumentos, devolvendo (valor, resto)."""
    resto = list(argv)
    if nome_flag not in resto:
        return None, resto
    idx = resto.index(nome_flag)
    if idx + 1 < len(resto):
        valor = resto[idx + 1]
        del resto[idx:idx + 2]
    else:
        valor = None
        del resto[idx]
    return valor, resto


def _cmd_natural(texto: str, root: Optional[Path] = None) -> int:
    deteccao = detectar_injecao(texto)
    if not deteccao.detectado or deteccao.intencao != 'injetar_componente':
        print("❌ Não foi possível detectar uma intenção de injeção de componente no texto.")
        print("   Use: python scripts/aidd_inject.py inject <tipo> <nome> --descricao '...'")
        return 1

    tipo = deteccao.argumentos_extras.get('tipo')
    descricao = deteccao.ideia_extraida
    nome = slug_a_partir_da_ideia(descricao)

    resultado = injetar(nome=nome, descricao=descricao, tipo=tipo, root=root)
    return _relatar(resultado)


def main(argv: Optional[List[str]] = None) -> int:
    argv = list(argv) if argv is not None else sys.argv[1:]

    if not argv:
        _build_parser().print_help()
        return 1

    if argv[0] == 'inject':
        parser = _build_parser()
        args = parser.parse_args(argv)
        return _cmd_inject(args)

    if argv[0] in ('-h', '--help'):
        _build_parser().print_help()
        return 0

    # Linguagem natural — extrai flags reconhecidas antes de tratar o resto como texto.
    root_valor, resto = _extrair_flag(argv, '--root')
    texto = ' '.join(resto)
    root = Path(root_valor) if root_valor else None
    return _cmd_natural(texto, root=root)


if __name__ == '__main__':
    sys.exit(main())
