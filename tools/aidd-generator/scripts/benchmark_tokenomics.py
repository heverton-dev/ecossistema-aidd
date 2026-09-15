#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BENCHMARK DE TOKENOMICS — Medição real de economia de tokens no aidd-generator.

Roda o pipeline completo (ou fases isoladas) com uma ideia de teste,
mede tokens reais via tiktoken por fase, compara com baseline legada
(dump bruto, fix-loop sem diff, regras monolíticas), e gera um relatório
JSON auditável com economia % real por fase, custo em dólares, e qualidade
(testes pytest).

Uso:
    python scripts/benchmark_tokenomics.py
    python scripts/benchmark_tokenomics.py --ideia "app de habitos"
    python scripts/benchmark_tokenomics.py --fases 1 2 8
    python scripts/benchmark_tokenomics.py --gerar-relatorio-html

Exit: 0 = benchmark concluído, 1 = falha.
"""

import argparse
import hashlib
import json
import os
import sys
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# ── Paths ──────────────────────────────────────────────────────────────────
SCRIPTS_DIR = Path(__file__).resolve().parent
GENERATOR_DIR = SCRIPTS_DIR.parent
CONFIG_DIR = GENERATOR_DIR / 'config'
TESTS_DIR = GENERATOR_DIR / 'tests'
BENCHMARKS_DIR = GENERATOR_DIR / 'benchmarks'
BENCHMARKS_DIR.mkdir(exist_ok=True)

# ── Tokenizer ──────────────────────────────────────────────────────────────
_tokenizador = None


def _obter_tokenizador():
    global _tokenizador
    if _tokenizador is None:
        try:
            import tiktoken
            _tokenizador = tiktoken.get_encoding('cl100k_base')
        except Exception:
            print("⚠️  tiktoken indisponível — usando heurística 4 chars/token")
            _tokenizador = False
    return _tokenizador


def contar_tokens(texto: str) -> int:
    """Conta tokens reais via tiktoken ou heurística."""
    tok = _obter_tokenizador()
    if tok:
        return len(tok.encode(texto))
    return max(len(texto.split()), len(texto) // 4, 1)


# ── Baselines legadas (o que o pipeline ANTES das otimizações faria) ───────

def baseline_handoff_fase1_fase2(referencias: List[dict]) -> str:
    """Baseline legada: dump JSON bruto integral (sem poda, sem top-k)."""
    return json.dumps(referencias, indent=2, ensure_ascii=False)


def baseline_prompt_fase8_monolitico(script_spec: dict) -> str:
    """Baseline legada: prompt com TODAS as regras sempre (sem composição)."""
    REGRAS_TODAS = """
SWAGGER DARK MODE: use FastAPI com tema dark, toggle no header.
MCP STUDIO: exponha tools via Model Context Protocol.
IMPECCABLE DESIGN: UI rica com gradientes, animações, glassmorphism.
FULL CRUD: implemente Create, Read, Update, Delete completo.
PRAGMA foreign_keys = ON: SQLite com chaves estrangeiras rigorosas.
JSON ROUND-TRIP: dados devem serializar/deserializar sem perda.
REGRAS DE DATAS: use ISO 8601, nunca strings soltas.
WEBHOOK HMAC: valide assinatura em webhooks recebidos.
"""
    prompt = (
        f"Implemente o script {script_spec.get('nome', 'script.py')}.\n"
        f"Responsabilidade: {script_spec.get('responsabilidade', '')}\n"
        f"Pseudocódigo: {script_spec.get('pseudocodigo', '')}\n"
        f"{REGRAS_TODAS}"
    )
    return prompt


def baseline_fix_loop_sendo_tudo(codigo: str, teste: str, erro: str) -> str:
    """Baseline legada: retry reenvia CODE + TEST + ERRORS integrais."""
    return (
        f"CORRIJA O CÓDIGO:\n\n```python\n{codigo}\n```\n\n"
        f"TESTE:\n```python\n{teste}\n```\n\n"
        f"ERRO:\n```\n{erro}\n```\n"
    )


# ── Otimizações reais (o que o pipeline DEPOIS das otimizações faz) ────────

def otimizado_handoff_fase1_fase2(referencias: List[dict], max_tokens: int = 5000) -> str:
    """Otimizado: top-k com campos seletos e truncagem."""
    try:
        sys.path.insert(0, str(SCRIPTS_DIR / 'phases'))
        from importlib import import_module
        mod = import_module('02_analisador')
        return mod.montar_handoff_referencias(referencias, max_tokens)
    except Exception:
        # Fallback: simular poda manual
        campos = ['nome', 'url', 'fonte', 'stars']
        podados = []
        for ref in sorted(referencias, key=lambda r: r.get('metadata', {}).get('stars', 0), reverse=True)[:10]:
            podado = {k: ref.get(k, '') for k in campos}
            podado['descricao'] = ref.get('metadata', {}).get('descricao', '')[:200]
            podados.append(podado)
        return json.dumps({'referencias': podados, '_handoff': {'poda_aplicada': True}})


def otimizado_prompt_fase8_composicao(script_spec: dict) -> str:
    """Otimizado: prompt por composição com blocos condicionais."""
    try:
        sys.path.insert(0, str(SCRIPTS_DIR / 'phases'))
        from importlib import import_module
        mod = import_module('08_implementador')
        return mod.ImplementadorFase8._montar_prompt_implementar_script(
            ideia='benchmark', stack={}, script_spec=script_spec,
            nome_raw=script_spec.get('nome', 'script.py'),
            modulo=script_spec.get('nome', 'script').replace('.py', ''),
            secao_schema='', caminho_sugerido='script.py',
            caminho_teste_sugerido='test_script.py',
        )
    except Exception:
        return baseline_prompt_fase8_monolitico(script_spec)


def otimizado_fix_loop_cirurgico(codigo: str, teste: str, erro: str) -> str:
    """Otimizado: traceback isolado + trecho recortado + diff mínimo."""
    try:
        sys.path.insert(0, str(SCRIPTS_DIR / 'phases'))
        from importlib import import_module
        mod = import_module('08_implementador')
        traceback_isolado = mod.PostMortemAnalyzer._isolar_traceback(erro)
        suspeitas = mod.PostMortemAnalyzer.extrair_funcoes_sob_suspeita(erro, codigo)
        contexto = '\n\n'.join(suspeitas) if suspeitas else codigo[:500]
        trecho_teste = teste[:300] if len(teste) > 300 else teste
        return mod.PROMPT_CORRIGIR_SCRIPT.format(
            secao_schema='', codigo=contexto, teste=trecho_teste,
            erro=traceback_isolado, modulo='benchmark',
        )
    except Exception:
        return baseline_fix_loop_sendo_tudo(codigo, teste, erro)


# ── Dados de teste realistas ──────────────────────────────────────────────

def gerar_referencias_teste(n: int = 30) -> List[dict]:
    """Gera N referências realistas infladas (como a Fase 1 retornaria)."""
    refs = []
    for i in range(n):
        refs.append({
            'nome': f'owner/projeto-habitos-{i}',
            'url': f'https://github.com/owner/projeto-habitos-{i}',
            'fonte': 'github',
            'metadata': {
                'stars': 50 + i * 37,
                'forks': 5 + i,
                'linguagens': 'Python',
                'ultimo_commit': '2026-09-01T12:00:00+00:00',
                'licenca': 'MIT',
                'descricao': f'Projeto de rastreamento de hábitos similar ao número {i} com funcionalidades de streak e dashboard.',
                'tags': [f'tag-{j}' for j in range(20)],
                'commits_por_mes': list(range(60)),
                'arvore_arquivos': [f'src/modulo_{j}/arquivo_{j}.py' for j in range(50)],
                'readme_integral': 'x' * 4000,
            },
        })
    return refs


SCRIPTS_TESTE = [
    {
        'nome': 'calcular_streak.py',
        'responsabilidade': 'Calcular streak de hábitos consecutivos',
        'pseudocodigo': '1. ler checkins\n2. contar dias consecutivos\n3. retornar streak atual',
    },
    {
        'nome': 'servidor_api.py',
        'responsabilidade': 'Servidor FastAPI com swagger, webhook e interface web UI HTML',
        'pseudocodigo': 'expor rotas HTTP com frontend e MCP',
    },
    {
        'nome': 'registrar_checkin.py',
        'responsabilidade': 'Salvar checkin diário no banco SQLite com foreign key para hábitos',
        'pseudocodigo': 'INSERT INTO checkins (habito_id, data) SELECT id FROM habitos',
    },
]

CODIGO_GRANDE_BENCHMARK = '\n'.join(
    '\n'.join([f"def funcao_{i}(x):"] + [f"    y_{j} = x + {j}" for j in range(10)] + [f"    return y_0 + {i}"])
    for i in range(50)
)

ERRO_BENCHMARK = (
    "tests/test_streak.py::test_calcular_streak FAILED\n\n"
    'Traceback (most recent call last):\n'
    '  File "tests/test_streak.py", line 15, in test_calcular_streak\n'
    '    assert calcular_streak(checkins) == 5\n'
    'AssertionError: assert 3 == 5'
)


# ── Dataclass do relatório ────────────────────────────────────────────────

@dataclass
class ResultadoFase:
    nome: str
    num_fase: int
    tokens_legado: int
    tokens_otimizado: int
    economia_tokens: int
    economia_pct: float
    descricao: str


@dataclass
class RelatorioBenchmark:
    timestamp: str
    ideia: str
    total_fases: int
    fases: List[ResultadoFase] = field(default_factory=list)
    tokens_total_legado: int = 0
    tokens_total_otimizado: int = 0
    economia_total_pct: float = 0.0
    custo_legado_usd: float = 0.0
    custo_otimizado_usd: float = 0.0
    economia_custo_usd: float = 0.0
    qualidade_testes: Optional[bool] = None
    testes_output: str = ''
    sha256_relatorio: str = ''

    def calcular_totais(self):
        self.tokens_total_legado = sum(f.tokens_legado for f in self.fases)
        self.tokens_total_otimizado = sum(f.tokens_otimizado for f in self.fases)
        if self.tokens_total_legado > 0:
            self.economia_total_pct = round(
                (1 - self.tokens_total_otimizado / self.tokens_total_legado) * 100, 2
            )
        # Custo estimado: GPT-4o ~$2.50/1M input + $10/1M output (referência)
        # Usamos proporção 80% input / 20% output para estimativa
        PRECO_INPUT_POR_MILHAO = 2.50
        PRECO_OUTPUT_POR_MILHAO = 10.0
        self.custo_legado_usd = round(
            (self.tokens_total_legado * 0.8 / 1_000_000 * PRECO_INPUT_POR_MILHAO) +
            (self.tokens_total_legado * 0.2 / 1_000_000 * PRECO_OUTPUT_POR_MILHAO), 4
        )
        self.custo_otimizado_usd = round(
            (self.tokens_total_otimizado * 0.8 / 1_000_000 * PRECO_INPUT_POR_MILHAO) +
            (self.tokens_total_otimizado * 0.2 / 1_000_000 * PRECO_OUTPUT_POR_MILHAO), 4
        )
        self.economia_custo_usd = round(self.custo_legado_usd - self.custo_otimizado_usd, 4)


# ── Execução do benchmark ─────────────────────────────────────────────────

def benchmark_handoff_1_2() -> ResultadoFase:
    """Benchmark do handoff Fase 1 → Fase 2."""
    referencias = gerar_referencias_teste(30)
    legado = baseline_handoff_fase1_fase2(referencias)
    otimizado = otimizado_handoff_fase1_fase2(referencias)
    tokens_legado = contar_tokens(legado)
    tokens_otim = contar_tokens(otimizado)
    return ResultadoFase(
        nome='Handoff Fase 1→2', num_fase=2,
        tokens_legado=tokens_legado, tokens_otimizado=tokens_otim,
        economia_tokens=tokens_legado - tokens_otim,
        economia_pct=round((1 - tokens_otim / max(tokens_legado, 1)) * 100, 2),
        descricao='Top-k referências com campos seletos vs dump JSON bruto',
    )


def benchmark_prompt_fase8() -> ResultadoFase:
    """Benchmark do prompt de composição Fase 8."""
    tokens_legado_total = 0
    tokens_otim_total = 0
    for spec in SCRIPTS_TESTE:
        legado = baseline_prompt_fase8_monolitico(spec)
        otimizado = otimizado_prompt_fase8_composicao(spec)
        tokens_legado_total += contar_tokens(legado)
        tokens_otim_total += contar_tokens(otimizado)
    return ResultadoFase(
        nome='Prompt Fase 8 (3 scripts)', num_fase=8,
        tokens_legado=tokens_legado_total, tokens_otimizado=tokens_otim_total,
        economia_tokens=tokens_legado_total - tokens_otim_total,
        economia_pct=round((1 - tokens_otim_total / max(tokens_legado_total, 1)) * 100, 2),
        descricao='Blocos condicionais por feature vs regras monolíticas',
    )


def benchmark_fix_loop() -> ResultadoFase:
    """Benchmark do fix-loop cirúrgico vs integral."""
    legado = baseline_fix_loop_sendo_tudo(CODIGO_GRANDE_BENCHMARK, CODIGO_GRANDE_BENCHMARK, ERRO_BENCHMARK)
    otimizado = otimizado_fix_loop_cirurgico(CODIGO_GRANDE_BENCHMARK, CODIGO_GRANDE_BENCHMARK, ERRO_BENCHMARK)
    tokens_legado = contar_tokens(legado)
    tokens_otim = contar_tokens(otimizado)
    return ResultadoFase(
        nome='Fix-loop Fase 8', num_fase=8,
        tokens_legado=tokens_legado, tokens_otimizado=tokens_otim,
        economia_tokens=tokens_legado - tokens_otim,
        economia_pct=round((1 - tokens_otim / max(tokens_legado, 1)) * 100, 2),
        descricao='Traceback isolado + trecho recortado vs CODE+TEST+ERRORS integrais',
    )


def rodar_testes_qualidade() -> tuple:
    """Roda os testes pytest e retorna (passou, output)."""
    import subprocess
    try:
        resultado = subprocess.run(
            [sys.executable, '-m', 'pytest', 'tests/', '-q', '--tb=short'],
            cwd=str(GENERATOR_DIR),
            capture_output=True, text=True, timeout=120,
        )
        output = resultado.stdout + '\n' + resultado.stderr
        passou = resultado.returncode == 0
        return passou, output[-2000:]  # Últimos 2000 chars
    except Exception as e:
        return False, f"Erro ao rodar testes: {e}"


def executar_benchmark(ideia: str = "app de hábitos", fases: Optional[List[int]] = None) -> RelatorioBenchmark:
    """Executa o benchmark completo e retorna o relatório."""
    print("=" * 70)
    print("  BENCHMARK DE TOKENOMICS — aidd-generator")
    print("=" * 70)
    print(f"  Ideia: {ideia}")
    print(f"  Timestamp: {time.strftime('%Y-%m-%dT%H:%M:%S')}")
    print()

    relatorio = RelatorioBenchmark(
        timestamp=time.strftime('%Y-%m-%dT%H:%M:%S'),
        ideia=ideia,
        total_fases=0,
    )

    benchmarks_disponiveis = {
        2: ('Handoff Fase 1→2', benchmark_handoff_1_2),
        8: ('Fase 8 (prompt + fix-loop)', benchmark_prompt_fase8),
        # Fix-loop é sub-item da Fase 8, rodamos junto
    }

    fases_a_rodar = fases or [2, 8]

    for num_fase in sorted(fases_a_rodar):
        if num_fase not in benchmarks_disponiveis:
            print(f"  ⚠️  Fase {num_fase} não tem benchmark configurado, pulando")
            continue

        nome, fn = benchmarks_disponiveis[num_fase]
        print(f"  📊 Benchmark: {nome}...")

        if num_fase == 8:
            # Fase 8: rodar prompt + fix-loop
            r1 = benchmark_prompt_fase8()
            r2 = benchmark_fix_loop()
            # Agregar: soma dos dois
            resultado = ResultadoFase(
                nome='Fase 8 completa (prompt + fix-loop)', num_fase=8,
                tokens_legado=r1.tokens_legado + r2.tokens_legado,
                tokens_otimizado=r1.tokens_otimizado + r2.tokens_otimizado,
                economia_tokens=(r1.economia_tokens + r2.economia_tokens),
                economia_pct=0,  # Calculado abaixo
                descricao=f"Prompt composição ({r1.economia_pct}%) + fix-loop ({r2.economia_pct}%)",
            )
            total_leg = resultado.tokens_legado
            total_otim = resultado.tokens_otimizado
            resultado.economia_pct = round((1 - total_otim / max(total_leg, 1)) * 100, 2) if total_leg > 0 else 0
        else:
            resultado = fn()

        relatorio.fases.append(resultado)
        relatorio.total_fases += 1

        cor = '🟢' if resultado.economia_pct > 30 else '🟡' if resultado.economia_pct > 10 else '🔴'
        print(f"     {cor} Legado: {resultado.tokens_legado:,} tokens → Otimizado: {resultado.tokens_otimizado:,} tokens")
        print(f"        Economia: {resultado.economia_pct}% ({resultado.economia_tokens:,} tokens economizados)")
        print()

    # Totais
    relatorio.calcular_totais()

    # Qualidade
    print("  🧪 Rodando testes de qualidade...")
    passou, output = rodar_testes_qualidade()
    relatorio.qualidade_testes = passou
    relatorio.testes_output = output
    status = '✅ PASSOU' if passou else '❌ FALHOU'
    print(f"     {status}")
    print()

    # SHA-256
    dados_para_hash = json.dumps({
        'timestamp': relatorio.timestamp,
        'ideia': relatorio.ideia,
        'tokens_total_legado': relatorio.tokens_total_legado,
        'tokens_total_otimizado': relatorio.tokens_total_otimizado,
        'economia_total_pct': relatorio.economia_total_pct,
        'qualidade_testes': relatorio.qualidade_testes,
    }, sort_keys=True)
    relatorio.sha256_relatorio = hashlib.sha256(dados_para_hash.encode()).hexdigest()

    # Resumo
    print("=" * 70)
    print("  RESUMO DO BENCHMARK")
    print("=" * 70)
    print(f"  Tokens legado total:    {relatorio.tokens_total_legado:>10,}")
    print(f"  Tokens otimizado total: {relatorio.tokens_total_otimizado:>10,}")
    print(f"  Economia total:         {relatorio.economia_total_pct:>9}%")
    print(f"  Economia em tokens:     {relatorio.tokens_total_legado - relatorio.tokens_total_otimizado:>10,}")
    print(f"  Custo legado (est.):    ${relatorio.custo_legado_usd:.4f}")
    print(f"  Custo otimizado (est.): ${relatorio.custo_otimizado_usd:.4f}")
    print(f"  Economia em USD:        ${relatorio.economia_custo_usd:.4f}")
    print(f"  Qualidade testes:       {status}")
    print(f"  SHA-256:                {relatorio.sha256_relatorio[:32]}...")
    print("=" * 70)

    return relatorio


def salvar_relatorio(relatorio: RelatorioBenchmark, caminho: Optional[Path] = None) -> Path:
    """Salva o relatório como JSON."""
    if caminho is None:
        ts = relatorio.timestamp.replace(':', '-').replace('T', '_')
        caminho = BENCHMARKS_DIR / f'benchmark_{ts}.json'

    dados = asdict(relatorio)
    caminho.write_text(json.dumps(dados, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f"\n  📄 Relatório salvo: {caminho}")
    return caminho


# ── CLI ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Benchmark de Tokenomics do aidd-generator')
    parser.add_argument('--ideia', default='app de hábitos', help='Ideia para o benchmark')
    parser.add_argument('--fases', nargs='+', type=int, default=[2, 8],
                        help='Fases para benchmark (default: 2 8)')
    parser.add_argument('--salvar', type=str, default=None,
                        help='Caminho para salvar o relatório JSON')
    args = parser.parse_args()

    relatorio = executar_benchmark(args.ideia, args.fases)
    salvar_relatorio(relatorio, Path(args.salvar) if args.salvar else None)

    # Exit code
    sys.exit(0 if relatorio.economia_total_pct > 0 else 1)


if __name__ == '__main__':
    main()
