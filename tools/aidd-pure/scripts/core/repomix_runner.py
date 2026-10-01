# -*- coding: utf-8 -*-
"""
REPOMIX RUNNER - AIDD Generator v2.2 (NIH #22)
Empacotador de contexto de repositorio para LLM delegando ao Repomix.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except (AttributeError, ValueError):
        pass


def estimar_tokens(texto: str) -> int:
    """Estima a contagem de tokens de forma deterministica (~4 caracteres por token)."""
    if not texto:
        return 0
    return max(1, len(texto) // 4)


def repomix_disponivel() -> bool:
    """Verifica se repomix ou npx esta disponivel no PATH."""
    if shutil.which('repomix'):
        return True
    if shutil.which('npx'):
        return True
    return False


def obter_comando_repomix() -> Optional[List[str]]:
    """Retorna o comando base para execucao do Repomix."""
    repomix_bin = shutil.which('repomix')
    if repomix_bin:
        return [repomix_bin]
    npx_bin = shutil.which('npx')
    if npx_bin:
        return [npx_bin, 'repomix']
    return None


def empacotar_metodo_antigo_caseiro(
    diretorio_alvo: Union[str, Path],
    includes: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Empacota arquivos no formato caseiro antigo (leitura crua arquivo a arquivo)."""
    diretorio = Path(diretorio_alvo)
    blocos = []
    arquivos_lidos = 0

    if not diretorio.exists():
        return {
            'status': 'FALHOU',
            'conteudo': '',
            'tamanho_chars': 0,
            'tokens_estimados': 0,
            'total_arquivos': 0,
            'ferramenta': 'metodo_antigo_caseiro'
        }

    padroes = includes if includes else ['src/**/*.py', 'tests/**/*.py', '*.py']
    arquivos_vistos = set()

    for padrao in padroes:
        for arq in diretorio.glob(padrao):
            if arq.is_file() and arq not in arquivos_vistos:
                arquivos_vistos.add(arq)
                try:
                    rel = arq.relative_to(diretorio)
                except ValueError:
                    rel = arq.name
                try:
                    conteudo = arq.read_text(encoding='utf-8', errors='replace')
                    blocos.append(f"MODULO: {rel}\nCODIGO:\n{conteudo}\n")
                    arquivos_lidos += 1
                except OSError:
                    pass

    resultado_texto = "\n".join(blocos)
    return {
        'status': 'SUCESSO',
        'conteudo': resultado_texto,
        'tamanho_chars': len(resultado_texto),
        'tokens_estimados': estimar_tokens(resultado_texto),
        'total_arquivos': arquivos_lidos,
        'ferramenta': 'metodo_antigo_caseiro'
    }


def empacotar_repositorio(
    diretorio_alvo: Union[str, Path],
    saida_arquivo: Optional[Union[str, Path]] = None,
    formato: str = 'xml',
    compress: bool = False,
    remove_comments: bool = False,
    remove_empty_lines: bool = False,
    no_file_summary: bool = True,
    includes: Optional[List[str]] = None,
    ignores: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Empacota repositorio ou subpasta usando o Repomix."""
    diretorio = Path(diretorio_alvo).resolve()
    if not diretorio.exists():
        return {
            'status': 'FALHOU',
            'erro': f'Diretorio nao encontrado: {diretorio}',
            'conteudo': '',
            'tamanho_chars': 0,
            'tokens_estimados': 0,
            'ferramenta': 'repomix'
        }

    cmd_base = obter_comando_repomix()

    if not cmd_base:
        fallback = empacotar_metodo_antigo_caseiro(diretorio, includes=includes)
        fallback['ferramenta'] = 'fallback_caseiro_sem_repomix'
        if saida_arquivo:
            out_p = Path(saida_arquivo)
            out_p.parent.mkdir(parents=True, exist_ok=True)
            out_p.write_text(fallback['conteudo'], encoding='utf-8')
            fallback['arquivo'] = str(out_p)
        return fallback

    if saida_arquivo:
        caminho_saida = Path(saida_arquivo).resolve()
    else:
        ext = 'xml' if formato == 'xml' else ('md' if formato == 'markdown' else 'txt')
        caminho_saida = (diretorio / f'repomix-output.{ext}').resolve()

    caminho_saida.parent.mkdir(parents=True, exist_ok=True)

    args = list(cmd_base)
    args.extend(['--style', formato])
    args.extend(['--output', str(caminho_saida)])

    if no_file_summary:
        args.append('--no-file-summary')
    if remove_comments:
        args.append('--remove-comments')
    if remove_empty_lines:
        args.append('--remove-empty-lines')
    if compress:
        args.append('--compress')
    if includes:
        args.extend(['--include', ','.join(includes)])
    if ignores:
        args.extend(['--ignore', ','.join(ignores)])

    try:
        usar_shell = sys.platform == 'win32'
        proc = subprocess.run(
            args,
            cwd=str(diretorio),
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            shell=usar_shell,
            timeout=120
        )
    except (subprocess.SubprocessError, OSError) as e:
        fallback = empacotar_metodo_antigo_caseiro(diretorio, includes=includes)
        fallback['ferramenta'] = 'fallback_erro_execucao'
        fallback['erro'] = str(e)
        return fallback

    if proc.returncode != 0 or not caminho_saida.exists():
        fallback = empacotar_metodo_antigo_caseiro(diretorio, includes=includes)
        fallback['ferramenta'] = 'fallback_repomix_returncode'
        fallback['erro'] = proc.stderr.strip() if proc.stderr else f'Exit code {proc.returncode}'
        return fallback

    try:
        conteudo = caminho_saida.read_text(encoding='utf-8', errors='replace')
    except OSError as e:
        return {
            'status': 'FALHOU',
            'erro': f'Falha ao ler arquivo do repomix: {e}',
            'conteudo': '',
            'tamanho_chars': 0,
            'tokens_estimados': 0,
            'ferramenta': 'repomix'
        }

    return {
        'status': 'SUCESSO',
        'conteudo': conteudo,
        'arquivo': str(caminho_saida),
        'tamanho_chars': len(conteudo),
        'tokens_estimados': estimar_tokens(conteudo),
        'formato': formato,
        'ferramenta': 'repomix',
        'comprimido': compress,
        'sem_comentarios': remove_comments,
        'sem_linhas_vazias': remove_empty_lines
    }


def comparar_empacotamento_tokens(
    diretorio_alvo: Union[str, Path],
    includes: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Compara consumo de caracteres e tokens entre metodo antigo e Repomix."""
    diretorio = Path(diretorio_alvo)

    antigo = empacotar_metodo_antigo_caseiro(diretorio, includes=includes)

    repomix_padrao = empacotar_repositorio(
        diretorio,
        formato='xml',
        no_file_summary=True,
        includes=includes
    )

    repomix_otimizado = empacotar_repositorio(
        diretorio,
        formato='xml',
        remove_comments=True,
        remove_empty_lines=True,
        no_file_summary=True,
        includes=includes
    )

    chars_antigo = antigo['tamanho_chars']
    tokens_antigo = antigo['tokens_estimados']

    chars_padrao = repomix_padrao['tamanho_chars']
    tokens_padrao = repomix_padrao['tokens_estimados']

    chars_otimizado = repomix_otimizado['tamanho_chars']
    tokens_otimizado = repomix_otimizado['tokens_estimados']

    economia_chars = max(0, chars_antigo - chars_otimizado)
    economia_tokens = max(0, tokens_antigo - tokens_otimizado)
    pct_economia = (economia_tokens / tokens_antigo * 100) if tokens_antigo > 0 else 0.0

    return {
        'diretorio': str(diretorio),
        'metodo_antigo': {
            'chars': chars_antigo,
            'tokens': tokens_antigo,
            'arquivos': antigo.get('total_arquivos', 0)
        },
        'repomix_padrao': {
            'chars': chars_padrao,
            'tokens': tokens_padrao,
            'ferramenta': repomix_padrao.get('ferramenta')
        },
        'repomix_otimizado': {
            'chars': chars_otimizado,
            'tokens': tokens_otimizado,
            'ferramenta': repomix_otimizado.get('ferramenta')
        },
        'economia_tokens': economia_tokens,
        'economia_chars': economia_chars,
        'reducao_tokens_pct': round(pct_economia, 2),
        'relatorio_texto': (
            f"Comparacao de Empacotamento de Contexto:\n"
            f"- Metodo antigo (concatenacao artesanal): {tokens_antigo} tokens ({chars_antigo} chars)\n"
            f"- Repomix XML padrao: {tokens_padrao} tokens ({chars_padrao} chars)\n"
            f"- Repomix XML otimizado (no-comments/no-empty): {tokens_otimizado} tokens ({chars_otimizado} chars)\n"
            f"- Economia de tokens gerada: {economia_tokens} tokens ({pct_economia:.1f}% de reducao)"
        )
    }
