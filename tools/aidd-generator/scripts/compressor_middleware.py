#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
COMPRESSOR MIDDLEWARE — Item 5 [TK-5]
Integração do pipeline com a skill sandeco-token-reduce (LLMLingua-2).

Política estrita (DoD item 3):
- Comprime SOMENTE prosa descritiva (resumos de referências, narrativas da
  Fase 6). NUNCA comprime código, JSON de schema, caminhos ou identificadores.
- Preflight: se LLMLingua-2 não estiver disponível, o pipeline segue com
  fallback determinístico transparente (truncamento por seção com elipse).
- Telemetria: toda compressão registra taxa real obtida (chars/tokens antes/depois).

Uso:
    from compressor_middleware import comprimir_se_compressivel, compressor_disponivel
    texto_menor, telemetria = comprimir_se_compressivel(resumo_em_prosa, contexto='handoff_fase1_fase2')
"""

import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Caminhos possíveis da skill sandeco-token-reduce (fonte física única do ecossistema)
_RAIZ_REPO = Path(__file__).resolve().parent.parent.parent.parent
SKILL_DIR = _RAIZ_REPO / 'componentes' / 'compartilhado' / 'skills' / 'sandeco-token-reduce'

# Taxa de compressão pedida ao LLMLingua-2 (0.4 = remove ~40% dos tokens)
TAXA_COMPRESSAO_PADRAO = 0.4
# Tamanho mínimo de prosa que justifica o custo de compressão
MIN_CHARS_COMPRIMIVEIS = 2000
# Alvo do critério de saída: redução >= 40% dos caracteres de prosa
ALVO_REDUCAO_MINIMA = 0.40


# =============================================================================
# PREFLIGHT — disponibilidade do compressor (zero custo quando ausente)
# =============================================================================

def compressor_disponivel() -> bool:
    """True se LLMLingua-2 está importável neste ambiente (preflight honesto)."""
    try:
        import llmlingua  # noqa: F401
        return True
    except ImportError:
        return False


def skill_presente() -> bool:
    """True se a skill sandeco-token-reduce está sincronizada no repositório."""
    return (SKILL_DIR / 'scripts' / 'compress.py').exists()


# =============================================================================
# POLÍTICA DECLARATIVA — o que NUNCA é comprimido
# =============================================================================

# Blocos que indicam código/esquema/caminho — proibidos de compressão
_PADRAO_PROIBIDO = (
    r'```',                       # code fence
    r'def\s+\w+\s*\(',            # assinatura python
    r'class\s+\w+[(:]',           # classe python
    r'INSERT\s+INTO|SELECT\s+.+\s+FROM',  # SQL
    r'\{["\']\w+["\']\s*:',       # JSON literal
    r'[A-Za-z]:\\\\|/src/|/tests/',  # caminhos
)

_PADRAO_PROIBIDO_COMPILADO = re.compile('|'.join(f'(?:{p})' for p in _PADRAO_PROIBIDO))


def eh_prosa_compressivel(texto: str) -> bool:
    """Política declarativa: True só para prosa descritiva livre.
    Código, JSON, SQL, caminhos e fences NUNCA são comprimidos."""
    if not isinstance(texto, str) or len(texto) < MIN_CHARS_COMPRIMIVEIS:
        return False
    return not _PADRAO_PROIBIDO_COMPILADO.search(texto)


# =============================================================================
# FALLBACK DETERMINÍSTICO — compressão estrutural sem ML
# =============================================================================

def _comprimir_fallback(texto: str) -> str:
    """Fallback determinístico (zero ML, zero rede): colapsa espaços,
    remove linhas e sentenças repetidas e corta parágrafos redundantes.
    Preserva a primeira ocorrência de cada sentença (informação de maior
    densidade). A dedup de sentenças cobre prosa repetitiva que chega como
    um único parágrafo (sem newlines), caso que a dedup por linha não pega."""
    linhas = [ln.strip() for ln in texto.splitlines()]
    # Remove linhas duplicadas consecutivas e vazias extras
    dedup = []
    for ln in linhas:
        if ln and ln == (dedup[-1] if dedup else None):
            continue
        dedup.append(ln)
    texto = '\n'.join(dedup)
    # Colapsa espaços múltiplos
    texto = re.sub(r'[ \t]{2,}', ' ', texto)
    # Dedup de sentenças dentro de cada parágrafo (mantém a 1ª ocorrência)
    paragrafos = []
    for bloco in re.split(r'\n\s*\n', texto):
        bloco = bloco.strip()
        if not bloco:
            continue
        sentencas = re.split(r'(?<=[.!?])\s+', bloco)
        vistas = set()
        unicas = []
        for s in sentencas:
            chave = s.strip().lower()
            if chave and chave in vistas:
                continue
            if chave:
                vistas.add(chave)
            unicas.append(s.strip())
        paragrafos.append(' '.join(s for s in unicas if s))
    # Corta parágrafos além da fração alvo (estrutura preservada)
    return '\n\n'.join(paragrafos[:max(1, int(len(paragrafos) * (1 - TAXA_COMPRESSAO_PADRAO)))])


# =============================================================================
# COMPRENSÃO VIA LLMLINGUA-2 (skill sandeco-token-reduce)
# =============================================================================

def _comprimir_llmlingua(texto: str, taxa: float) -> Optional[str]:
    """Compressão real via LLMLingua-2. None se falhar (caller faz fallback)."""
    try:
        from llmlingua import PromptCompressor
    except ImportError:
        return None
    try:
        compressor = PromptCompressor(
            model_name='microsoft/llmlingua-2-bert-base-multilingual-cased-meetingbank',
            use_llmlingua2=True,
        )
        resultado = compressor.compress_prompt(texto, rate=taxa)
        comprimido = resultado.get('compressed_prompt')
        return comprimido if isinstance(comprimido, str) and comprimido.strip() else None
    except Exception as e:
        print(f"⚠️  Compressor LLMLingua-2 falhou ({e}); usando fallback determinístico",
              file=sys.stderr)
        return None


# =============================================================================
# ENTRYPOINT DO MIDDLEWARE
# =============================================================================

def comprimir_se_compressivel(texto: str,
                              contexto: str = '',
                              taxa: float = TAXA_COMPRESSAO_PADRAO) -> tuple:
    """Comprime texto de prosa via sandeco-token-reduce; caso contrário devolve
    o texto original com telemetria indicando que nada foi comprimido.

    Returns:
        (texto_final, telemetria) onde telemetria = {
            'comprimido': bool, 'metodo': str, 'contexto': str,
            'caracteres_antes': int, 'caracteres_depois': int,
            'taxa_reducao_real': float, 'duracao_ms': int
        }
    """
    t0 = time.perf_counter()
    antes = len(texto or '')

    telemetria: Dict[str, Any] = {
        'comprimido': False,
        'metodo': 'nenhum',
        'contexto': contexto,
        'caracteres_antes': antes,
        'caracteres_depois': antes,
        'taxa_reducao_real': 0.0,
        'duracao_ms': 0,
    }

    if not eh_prosa_compressivel(texto or ''):
        # Política: código/JSON/texto curto passa intacto
        telemetria['metodo'] = 'nao_compressivel_pela_politica'
        return texto, telemetria

    comprimido = None
    if compressor_disponivel():
        try:
            comprimido = _comprimir_llmlingua(texto, taxa)
            if comprimido is not None:
                telemetria['metodo'] = 'llmlingua2'
        except Exception as e:
            # Qualquer falha do ML cai no fallback determinístico (resiliência total)
            print(f"⚠️  Compressor falhou ({e}); usando fallback determinístico", file=sys.stderr)
            comprimido = None
    if comprimido is None and telemetria['metodo'] == 'nenhum':
        comprimido = _comprimir_fallback(texto)
        telemetria['metodo'] = 'fallback_deterministico'

    depois = len(comprimido)
    telemetria.update({
        'comprimido': depois < antes,
        'caracteres_depois': depois,
        'taxa_reducao_real': round((antes - depois) / antes, 4) if antes else 0.0,
        'duracao_ms': int((time.perf_counter() - t0) * 1000),
    })
    return comprimido, telemetria
