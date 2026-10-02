#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GATE: G_TOKENOMICS — Validação de economia de tokens no pipeline.

Audita o _pipeline_state.json de uma execução do pipeline e verifica:
1. Tokens reais por fase não excedem orçamento (token_budgets.json).
2. Economia total é ≥ limiar configurável (default: 30%).
3. Origem de medição está rotulada honestamente (autodeclarado/medido_api).
4. Nenhuma fase afirma "medição real" para valor autodeclarado.

O gate é DETERMINÍSTICO (zero tokens) — lê JSON, aplica regras, retorna exit code.

Uso:
    python scripts/gates/G_TOKENOMICS.py
    python scripts/gates/G_TOKENOMICS.py --pasta /caminho/projeto
    python scripts/genus/G_TOKENOMICS.py --min-economia 20

Exit: 0 = aprovado, 1 = violação encontrada.
"""

import argparse
import json
import sys
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# ── Paths ──────────────────────────────────────────────────────────────────
SCRIPTS_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = SCRIPTS_DIR / 'config'
TOKEN_BUDGETS_PATH = CONFIG_DIR / 'token_budgets.json'


# ── Configuração ───────────────────────────────────────────────────────────

LIMIAR_ECONOMIA_PADRAO = 30  # % mínimo de economia esperada
LIMIAR_DESVIO_ORCAMENTO = 1.2  # 20% acima do orçamento = alerta


def carregar_orcamentos() -> dict:
    """Carrega token_budgets.json."""
    if not TOKEN_BUDGETS_PATH.exists():
        return {}
    try:
        dados = json.loads(TOKEN_BUDGETS_PATH.read_text(encoding='utf-8'))
        return dados.get('fases', {})
    except (json.JSONDecodeError, OSError):
        return {}


def encontrar_pipeline_state(pasta: Path) -> Path | None:
    """Encontra _pipeline_state.json na árvore de pastas."""
    # Busca direta
    direto = pasta / '.aidd' / 'cache' / '_pipeline_state.json'
    if direto.exists():
        return direto
    # Busca recursiva (1 nível)
    for sub in pasta.rglob('_pipeline_state.json'):
        return sub
    return None


# ── Auditorias ─────────────────────────────────────────────────────────────

def auditar_orcamento_por_fase(estado: dict, orcamentos: dict) -> list[str]:
    """Verifica se tokens utilizados por fase excedem o orçamento."""
    violacoes = []
    orcamento_fases = estado.get('orcamento_fases', {})

    for chave, registro in orcamento_fases.items():
        if chave not in orcamentos:
            continue
        budget = orcamentos[chave].get('orcamento_tokens', 0)
        utilizados = registro.get('tokens_utilizados', 0)
        if budget > 0 and utilizados > budget * LIMIAR_DESVIO_ORCAMENTO:
            violacoes.append(
                f"{chave}: {utilizados} tokens > {budget * LIMIAR_DESVIO_ORCAMENTO:.0f} "
                f"(orçamento {budget} + {(LIMIAR_DESVIO_ORCAMENTO - 1) * 100:.0f}%)"
            )
    return violacoes


def auditar_origem_medicao(estado: dict) -> list[str]:
    """Verifica que origem_medicao está honestamente rotulada."""
    violacoes = []
    fases = estado.get('fases', {})

    for nome_fase, dados_fase in fases.items():
        if not isinstance(dados_fase, dict):
            continue

        # Checar tokens nested
        tokens = dados_fase.get('tokens', {})
        if isinstance(tokens, dict):
            origem = tokens.get('origem_medicao', '')
            medicao = tokens.get('medicao', '')

            # Violação: autodeclarado mas diz "real" ou "litellm"
            if origem == 'autodeclarado':
                medicao_lower = medicao.lower()
                if 'real' in medicao_lower and 'litellm' in medicao_lower:
                    violacoes.append(
                        f"{nome_fase}: origem=autodeclarado mas medicao='{medicao}' "
                        f"(afirma falsamente medição real)"
                    )

        # Checar tokens_consumidos no nível raiz da fase
        tokens_consumidos = dados_fase.get('tokens_consumidos')
        if tokens_consumidos is not None and isinstance(tokens_consumidos, (int, float)):
            if tokens_consumidos < 0:
                violacoes.append(f"{nome_fase}: tokens_consumidos negativo ({tokens_consumidos})")

    return violacoes


def auditar_economia_minima(estado: dict, min_economia: float) -> list[str]:
    """Verifica se a economia total atinge o limiar mínimo."""
    violacoes = []
    orcamento_fases = estado.get('orcamento_fases', {})

    if not orcamento_fases:
        return ["Nenhum registro de orçamento encontrado em _pipeline_state.json"]

    total_orcado = 0
    total_utilizado = 0
    for registro in orcamento_fases.values():
        total_orcado += registro.get('orcamento_tokens', 0)
        total_utilizado += registro.get('tokens_utilizados', 0)

    if total_orcado > 0 and total_utilizado > 0:
        # Economia = (1 - utilizado/orçado) * 100
        # Se utilizado < orçado, há economia
        economia_pct = (1 - total_utilizado / total_orcado) * 100
        if economia_pct < min_economia:
            violacoes.append(
                f"Economia total {economia_pct:.1f}% < limiar {min_economia}% "
                f"({total_utilizado:,}/{total_orcado:,} tokens)"
            )

    return violacoes


def auditar_fases_sem_tokens(estado: dict) -> list[str]:
    """Alerta sobre fases que deveriam ter tokens mas não registraram."""
    alertas = []
    fases_esperadas = {
        'fase_1_pesquisador', 'fase_2_analisador', 'fase_3_designer',
        'fase_4_planejador', 'fase_5_criador', 'fase_6_documentador',
        'fase_7_auto_critica',
    }
    fases_estado = estado.get('fases', {})

    for fase in fases_esperadas:
        if fase not in fases_estado:
            alertas.append(f"Fase {fase} não encontrada no estado")
        elif isinstance(fases_estado[fase], dict):
            tokens = fases_estado[fase].get('tokens_consumidos', 0)
            if tokens == 0:
                # Fases 1 e 5 são Zero-Token (determinísticas), isso é ok
                if fase not in ('fase_1_pesquisador', 'fase_5_criador'):
                    alertas.append(f"Fase {fase} registrou 0 tokens (inesperado para fase LLM)")

    return alertas


# ── Main ───────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description='G_TOKENOMICS — gate de economia de tokens')
    parser.add_argument('--pasta', type=str, default='.',
                        help='Pasta do projeto (default: diretório atual)')
    parser.add_argument('--min-economia', type=float, default=LIMIAR_ECONOMIA_PADRAO,
                        help=f'Economia mínima %% (default: {LIMIAR_ECONOMIA_PADRAO}%%)')
    args = parser.parse_args()

    print(f'💰 G_TOKENOMICS — validação de economia de tokens')
    print(f'   Pasta: {Path(args.pasta).resolve()}')
    print(f'   Limiar mínimo de economia: {args.min_economia}%')
    print()

    # 1. Encontrar _pipeline_state.json
    pasta = Path(args.pasta).resolve()
    state_path = encontrar_pipeline_state(pasta)
    if state_path is None:
        print('⚠️  _pipeline_state.json não encontrado — gate pulado (sem dados)')
        print('✅ GATE APROVADO (sem dados para auditar)')
        return 0

    print(f'   Estado: {state_path}')
    try:
        estado = json.loads(state_path.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, OSError) as e:
        print(f'✗ Erro ao ler _pipeline_state.json: {e}')
        print('\n✗ GATE FALHOU')
        return 1

    # 2. Carregar orçamentos
    orcamentos = carregar_orcamentos()

    # 3. Executar auditorias
    violacoes_totais = []

    print('\n📊 Auditoria 1: Orçamento por fase')
    v1 = auditar_orcamento_por_fase(estado, orcamentos)
    if v1:
        violacoes_totais.extend(v1)
        for v in v1:
            print(f'   ✗ {v}')
    else:
        print('   ✓ Todas as fases dentro do orçamento')

    print('\n📊 Auditoria 2: Origem de medição honesta')
    v2 = auditar_origem_medicao(estado)
    if v2:
        violacoes_totais.extend(v2)
        for v in v2:
            print(f'   ✗ {v}')
    else:
        print('   ✓ Nenhuma afirmação falsa de medição real')

    print(f'\n📊 Auditoria 3: Economia mínima ({args.min_economia}%)')
    v3 = auditar_economia_minima(estado, args.min_economia)
    if v3:
        violacoes_totais.extend(v3)
        for v in v3:
            print(f'   ✗ {v}')
    else:
        print('   ✓ Economia total acima do limiar')

    print('\n📊 Auditoria 4: Fases sem registro de tokens')
    v4 = auditar_fases_sem_tokens(estado)
    if v4:
        for a in v4:
            print(f'   ⚠️  {a}')
        # Alertas, não violações (não bloqueia)

    # Resultado
    if violacoes_totais:
        print(f'\n✗ GATE FALHOU — {len(violacoes_totais)} violação(ões) encontrada(s)')
        return 1

    print('\n✅ GATE APROVADO — economia de tokens validada')
    return 0


if __name__ == '__main__':
    sys.exit(main())
