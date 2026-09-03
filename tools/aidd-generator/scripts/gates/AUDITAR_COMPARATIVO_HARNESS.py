#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GATE: AUDITAR_COMPARATIVO_HARNESS — Auditoria mecânica de projetos gerados
por múltiplos harness a partir do MESMO prompt (aidd-project-generator).

100% Python determinístico, zero LLM: toda métrica vem de arquivo real
(git log, _phase_0N_index.json, filesystem) ou é claramente rotulada
como "autodeclarado" quando não pode ser verificada de forma
independente (tempo/tokens só o harness sabe).

Uso:
    python scripts/gates/AUDITAR_COMPARATIVO_HARNESS.py \
        --raiz .. --nome-projeto habit-tracker-cli

Convenção de pasta esperada (irmã do repo aidd-project-generator):
    <HARNESS>_<nome-projeto>/   ex: CLAUDE-CODE_habit-tracker-cli

Princípio AIDD aplicado: Zero Alucinação — nenhum número neste relatório
é inventado; o que não pode ser medido é rotulado como tal, nunca
apresentado como fato.
"""

import sys
import json
import subprocess
import argparse
from pathlib import Path
from datetime import datetime, timezone

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


# =============================================================================
# COLETA (100% leitura de arquivo real / comando git — zero LLM)
# =============================================================================

def _ler_json(path: Path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None


def _git_timestamps(pasta: Path):
    """Timestamp do primeiro e último commit — cross-check objetivo do
    tempo autodeclarado pelo harness. Retorna None se não for repo git."""
    try:
        primeiro = subprocess.run(
            ['git', 'log', '--reverse', '--format=%aI', ],
            cwd=str(pasta), capture_output=True, text=True, encoding='utf-8',
            errors='replace', timeout=10
        )
        if primeiro.returncode != 0 or not primeiro.stdout.strip():
            return None, None, 0
        linhas = primeiro.stdout.strip().splitlines()
        ts_inicio = linhas[0]
        ts_fim = linhas[-1]
        return ts_inicio, ts_fim, len(linhas)
    except Exception:
        return None, None, 0


def _contar_arquivos(pasta: Path):
    arquivos = sum(1 for f in pasta.rglob('*') if f.is_file() and '.git' not in f.parts)
    diretorios = sum(1 for d in pasta.rglob('*') if d.is_dir() and '.git' not in d.parts)
    return arquivos, diretorios


def _verificar_symlink_agents(pasta: Path):
    """Zero Duplicidade: AGENTS.md deve existir e .claude/CLAUDE.md deve
    ser symlink real para ele (ou cópia honesta se o SO negou privilégio
    — ambos são aceitáveis, o que NÃO é aceitável é conteúdo divergente)."""
    agents = pasta / 'AGENTS.md'
    claude_md = pasta / '.claude' / 'CLAUDE.md'
    if not agents.exists() or not claude_md.exists():
        return {'presente': False, 'symlink_real': False, 'conteudo_consistente': False}

    symlink_real = claude_md.is_symlink()
    try:
        consistente = agents.read_text(encoding='utf-8') == claude_md.read_text(encoding='utf-8')
    except Exception:
        consistente = False

    return {'presente': True, 'symlink_real': symlink_real, 'conteudo_consistente': consistente}


def _verificar_documentacao(pasta: Path):
    output_dirs = list((pasta / 'output').glob('*/documentos')) if (pasta / 'output').exists() else []
    formatos = {'html': False, 'md': False, 'pdf': False}
    if output_dirs:
        docs_dir = output_dirs[0]
        formatos['html'] = any(docs_dir.glob('*.html'))
        formatos['md'] = any(docs_dir.glob('*.md'))
        formatos['pdf'] = any(docs_dir.glob('*.pdf'))
    return formatos


def _coletar_fases(pasta: Path):
    """Lê os 7 _phase_0N_index.json reais — completude e gates são
    medidos daqui, nunca assumidos."""
    cache = pasta / '.aidd' / 'cache'
    fases = {}
    for i in range(1, 8):
        idx = _ler_json(cache / f'_phase_{i:02d}_index.json')
        fases[f'fase_{i}'] = idx
    return fases


def coletar_projeto(pasta: Path) -> dict:
    """Coleta todos os dados objetivos + autodeclarados de um projeto gerado."""
    nome_pasta = pasta.name
    harness_da_pasta = nome_pasta.split('_', 1)[0] if '_' in nome_pasta else 'desconhecido'

    config = _ler_json(pasta / '.aidd' / 'config.json') or {}
    settings = _ler_json(pasta / '.claude' / 'settings.json') or {}
    autodeclarado = _ler_json(pasta / 'RELATORIO-EXECUCAO-HARNESS.json')

    ts_inicio, ts_fim, total_commits = _git_timestamps(pasta)
    duracao_git_segundos = None
    if ts_inicio and ts_fim:
        try:
            t0 = datetime.fromisoformat(ts_inicio)
            t1 = datetime.fromisoformat(ts_fim)
            duracao_git_segundos = (t1 - t0).total_seconds()
        except ValueError:
            pass

    arquivos, diretorios = _contar_arquivos(pasta)
    fases = _coletar_fases(pasta)
    fases_completas = sum(1 for f in fases.values() if f and f.get('status') == 'COMPLETO')

    total_gates = 0
    gates_passaram = 0
    for f in fases.values():
        if not f:
            continue
        for g in f.get('gates_executados', []):
            total_gates += 1
            if g.get('status') == 'PASSOU':
                gates_passaram += 1

    score_auto_critica = None
    fase7 = fases.get('fase_7')
    if fase7:
        score_auto_critica = fase7.get('processamento', {}).get('score_calculado')

    return {
        'pasta': str(pasta),
        'harness_declarado_pela_pasta': harness_da_pasta,
        'harness_config_json': config.get('harness', 'desconhecido'),
        'harness_settings_json': settings.get('harness', 'desconhecido'),
        'modelo_config_json': config.get('lm', 'desconhecido'),
        'modelo_settings_json': settings.get('modelo', 'desconhecido'),
        'autodeclarado': autodeclarado,
        'git': {
            'total_commits': total_commits,
            'primeiro_commit_utc': ts_inicio,
            'ultimo_commit_utc': ts_fim,
            'duracao_estimada_segundos': duracao_git_segundos,
        },
        'filesystem': {
            'total_arquivos': arquivos,
            'total_diretorios': diretorios,
        },
        'pipeline': {
            'fases_completas': fases_completas,
            'total_fases': 7,
            'gates_total': total_gates,
            'gates_passaram': gates_passaram,
            'score_auto_critica': score_auto_critica,
        },
        'zero_duplicidade': _verificar_symlink_agents(pasta),
        'documentacao': _verificar_documentacao(pasta),
    }


# =============================================================================
# SCORE MECÂNICO (determinístico — sem juízo de LLM)
# =============================================================================

def calcular_score(dados: dict) -> dict:
    """Score 0-100 por critério, só a partir de dado objetivamente medido
    neste script (nunca do que o harness autodeclarou)."""
    dimensoes = {}

    dimensoes['completude_pipeline'] = int(
        (dados['pipeline']['fases_completas'] / dados['pipeline']['total_fases']) * 100
    )

    gates_total = dados['pipeline']['gates_total']
    dimensoes['qualidade_gates'] = int(
        (dados['pipeline']['gates_passaram'] / gates_total) * 100
    ) if gates_total else 0

    dimensoes['score_auto_critica'] = dados['pipeline']['score_auto_critica'] or 0

    formatos = dados['documentacao']
    dimensoes['documentacao'] = int(sum(formatos.values()) / 3 * 100)

    zd = dados['zero_duplicidade']
    dimensoes['zero_duplicidade'] = 100 if (zd['presente'] and zd['conteudo_consistente']) else (
        50 if zd['presente'] else 0
    )

    # Consistência de identidade: pasta / config.json / settings.json devem
    # concordar sobre qual harness gerou o projeto (prova que a correção de
    # 'harness hardcoded Claude Code' realmente funcionou nesta execução)
    identidades = {
        dados['harness_declarado_pela_pasta'].lower(),
        dados['harness_config_json'].lower(),
        dados['harness_settings_json'].lower(),
    }
    dimensoes['consistencia_identidade'] = 100 if len(identidades) == 1 else 0

    pesos = {
        'completude_pipeline': 30,
        'qualidade_gates': 25,
        'score_auto_critica': 20,
        'documentacao': 10,
        'zero_duplicidade': 10,
        'consistencia_identidade': 5,
    }
    total = sum(dimensoes[d] * pesos[d] for d in dimensoes) / sum(pesos.values())

    return {'total': round(total, 1), 'por_dimensao': dimensoes}


# =============================================================================
# RELATÓRIO EM PROSA (template determinístico — não gerado por LLM)
# =============================================================================

def gerar_prosa(dados: dict, score: dict) -> str:
    harness = dados['harness_declarado_pela_pasta']
    partes = []

    if score['por_dimensao']['consistencia_identidade'] == 0:
        partes.append(
            f"ATENÇÃO: a pasta declara harness '{dados['harness_declarado_pela_pasta']}', mas o "
            f"config.json diz '{dados['harness_config_json']}' e settings.json diz "
            f"'{dados['harness_settings_json']}' — identidade inconsistente, investigar antes de "
            f"confiar em qualquer outra métrica deste projeto."
        )

    fc = dados['pipeline']['fases_completas']
    if fc == 7:
        partes.append(f"{harness} completou as 7 fases do pipeline sem interrupção.")
    else:
        partes.append(f"{harness} completou apenas {fc}/7 fases — pipeline não chegou ao fim.")

    gp, gt = dados['pipeline']['gates_passaram'], dados['pipeline']['gates_total']
    if gt:
        taxa = gp / gt * 100
        if taxa == 100:
            partes.append(f"Todos os {gt} gates mecânicos passaram, sem exceção.")
        else:
            partes.append(f"{gp}/{gt} gates passaram ({taxa:.0f}%) — houve pelo menos uma falha real de validação.")

    sc = dados['pipeline']['score_auto_critica']
    if sc is not None:
        partes.append(f"A auto-crítica da Fase 7 (calculada pelo próprio pipeline, não por este auditor) deu {sc}/100.")

    zd = dados['zero_duplicidade']
    if zd['presente'] and zd['symlink_real']:
        partes.append("AGENTS.md→CLAUDE.md é um symlink real (Zero Duplicidade cumprida na prática, não só na intenção).")
    elif zd['presente'] and not zd['symlink_real']:
        partes.append("AGENTS.md→CLAUDE.md caiu para cópia de conteúdo (SO negou privilégio de symlink) — consistente, mas não é um symlink de verdade.")
    else:
        partes.append("AGENTS.md ou .claude/CLAUDE.md ausente — padrão Zero Duplicidade não aplicado.")

    docs = dados['documentacao']
    n_formatos = sum(docs.values())
    partes.append(f"Documentação tripartite: {n_formatos}/3 formatos gerados ({', '.join(k for k,v in docs.items() if v) or 'nenhum'}).")

    if dados['autodeclarado']:
        auto = dados['autodeclarado']
        tempo = auto.get('timestamps', {}).get('duracao_segundos')
        tokens = auto.get('tokens', {})
        partes.append(
            f"Segundo autodeclaração do próprio harness (não verificável de forma independente): "
            f"{tempo}s de execução, {tokens.get('total', 'N/D')} tokens totais "
            f"(fonte: {tokens.get('fonte', 'não especificada')})."
        )
        git_dur = dados['git']['duracao_estimada_segundos']
        if git_dur is not None and tempo is not None:
            diff_pct = abs(git_dur - tempo) / max(tempo, 1) * 100
            if diff_pct > 50:
                partes.append(
                    f"Aviso: o intervalo entre primeiro e último commit ({git_dur:.0f}s) diverge "
                    f"{diff_pct:.0f}% do tempo autodeclarado — considerar o tempo autodeclarado com cautela."
                )
    else:
        partes.append("Nenhum RELATORIO-EXECUCAO-HARNESS.json encontrado — tempo e tokens não foram autodeclarados, e não há como medi-los de forma independente a posteriori.")

    return ' '.join(partes)


# =============================================================================
# INTEGRIDADE DO REPOSITÓRIO-FERRAMENTA (não dos projetos gerados)
# =============================================================================

ARQUIVOS_NUCLEO_PROTEGIDOS = (
    'scripts/phases/',
    'scripts/pipeline_completo.py',
    'scripts/gates/',
)


def verificar_integridade_ferramenta(desde_commit: str = None) -> list:
    """Verifica se algum harness tocou o núcleo compartilhado da ferramenta
    (scripts/phases, scripts/gates, pipeline_completo.py) durante o teste —
    achado real (2026-08-30): um harness commitou uma mudança de risco no
    protocolo delegado que afetaria TODOS os outros harness igualmente.
    Isso não julga se a mudança era legítima, só torna visível — cabe a
    quem lê o relatório decidir se foi um fix real ou um hack.
    """
    intervalo = f'{desde_commit}..HEAD' if desde_commit else '-20'
    args = ['git', 'log', '--format=%H|%ai|%s']
    args += [intervalo] if desde_commit else ['-n', '20']

    resultado = subprocess.run(args, capture_output=True, text=True,
                                encoding='utf-8', errors='replace', timeout=10)
    if resultado.returncode != 0:
        return []

    achados = []
    for linha in resultado.stdout.strip().splitlines():
        partes = linha.split('|', 2)
        if len(partes) != 3:
            continue
        commit_hash, data, mensagem = partes

        arquivos = subprocess.run(
            ['git', 'show', '--name-only', '--format=', commit_hash],
            capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=10
        ).stdout.strip().splitlines()

        tocados = [a for a in arquivos if any(a.startswith(p) for p in ARQUIVOS_NUCLEO_PROTEGIDOS)]
        if tocados:
            achados.append({
                'commit': commit_hash[:8],
                'data': data,
                'mensagem': mensagem,
                'arquivos_nucleo_tocados': tocados,
            })

    return achados


# =============================================================================
# RELATÓRIO MARKDOWN
# =============================================================================

def gerar_relatorio_markdown(resultados: list, integridade_ferramenta: list = None) -> str:
    md = ["# Auditoria Comparativa de Harness — aidd-project-generator\n"]
    md.append(f"_Gerado em {datetime.now(timezone.utc).isoformat()} por AUDITAR_COMPARATIVO_HARNESS.py (100% determinístico, zero LLM)_\n")

    if integridade_ferramenta:
        md.append("\n## ⚠️ Mudanças no núcleo da ferramenta durante o teste\n")
        md.append(
            "Os commits abaixo tocaram `scripts/phases/`, `scripts/gates/` ou "
            "`scripts/pipeline_completo.py` — o núcleo COMPARTILHADO usado por "
            "todos os harness. Isso não é necessariamente um problema (pode ser "
            "correção legítima), mas precisa ser revisado manualmente antes de "
            "confiar nos resultados — uma mudança de risco aqui afeta todos os "
            "harness igualmente, não só quem commitou.\n"
        )
        for a in integridade_ferramenta:
            md.append(f"- `{a['commit']}` ({a['data']}) — {a['mensagem']}")
            for arq in a['arquivos_nucleo_tocados']:
                md.append(f"  - {arq}")
    else:
        md.append("\n✅ Nenhuma mudança no núcleo da ferramenta detectada durante a janela verificada.\n")

    md.append("\n## Tabela Comparativa\n")
    md.append("| Harness | LLM (config.json) | Fases | Gates | Score Auto-Crítica | Score Auditoria | Tempo (autodeclarado) | Tokens (autodeclarado) |")
    md.append("|---|---|---|---|---|---|---|---|")
    for r in resultados:
        d, s = r['dados'], r['score']
        auto = d['autodeclarado'] or {}
        tempo = auto.get('timestamps', {}).get('duracao_segundos', 'N/D')
        tokens = auto.get('tokens', {}).get('total', 'N/D')
        md.append(
            f"| {d['harness_declarado_pela_pasta']} | {d['modelo_config_json']} | "
            f"{d['pipeline']['fases_completas']}/7 | {d['pipeline']['gates_passaram']}/{d['pipeline']['gates_total']} | "
            f"{d['pipeline']['score_auto_critica']} | {s['total']} | {tempo}s | {tokens} |"
        )

    md.append("\n**Nota de transparência:** \"Tempo\" e \"Tokens\" são autodeclarados pelo próprio harness — este auditor não tem acesso independente ao consumo real de API de outro processo. \"Score Auditoria\" é 100% mecânico (completude + gates + auto-crítica + docs + zero-duplicidade + consistência de identidade), nunca um julgamento de LLM.\n")

    for r in resultados:
        d, s = r['dados'], r['score']
        md.append(f"\n---\n\n## {d['harness_declarado_pela_pasta']}\n")
        md.append(f"**Pasta:** `{d['pasta']}`\n")
        md.append(f"\n### Notas por critério (0-100, mecânico)\n")
        for k, v in s['por_dimensao'].items():
            md.append(f"- **{k}**: {v}")
        md.append(f"\n**Nota geral: {s['total']}/100**\n")
        md.append(f"\n### Análise\n\n{r['prosa']}\n")

    return '\n'.join(md)


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Auditoria comparativa determinística de projetos gerados por múltiplos harness'
    )
    parser.add_argument('--raiz', default='..', help='Pasta onde procurar <HARNESS>_<projeto>/ (default: pasta pai)')
    parser.add_argument('--nome-projeto', required=True, help='Sufixo do nome do projeto (ex: habit-tracker-cli)')
    parser.add_argument('--saida', default='RELATORIO-COMPARATIVO-HARNESS.md', help='Arquivo de saída')
    parser.add_argument('--desde-commit', default=None,
                       help='Verificar integridade do núcleo da ferramenta desde este commit (default: últimos 20 commits)')

    args = parser.parse_args()
    raiz = Path(args.raiz).resolve()

    print("🔒 Verificando integridade do núcleo da ferramenta...")
    integridade = verificar_integridade_ferramenta(args.desde_commit)
    if integridade:
        print(f"   ⚠️  {len(integridade)} commit(s) tocaram arquivos protegidos — revise antes de confiar no resultado.")
    else:
        print("   ✅ Nenhuma mudança suspeita no núcleo detectada.")
    print("")

    pastas = sorted(p for p in raiz.glob(f'*_{args.nome_projeto}') if p.is_dir())

    if not pastas:
        print(f"❌ Nenhuma pasta '*_{args.nome_projeto}' encontrada em {raiz}")
        sys.exit(1)

    print(f"🔍 Encontradas {len(pastas)} pasta(s): {[p.name for p in pastas]}\n")

    resultados = []
    for pasta in pastas:
        print(f"📊 Auditando {pasta.name}...")
        dados = coletar_projeto(pasta)
        score = calcular_score(dados)
        prosa = gerar_prosa(dados, score)
        resultados.append({'dados': dados, 'score': score, 'prosa': prosa})
        print(f"   Score: {score['total']}/100")

    relatorio = gerar_relatorio_markdown(resultados, integridade)
    Path(args.saida).write_text(relatorio, encoding='utf-8')
    print(f"\n✅ Relatório salvo em: {args.saida}")

    # JSON bruto também, para quem quiser processar os dados sem parsear MD
    saida_json = Path(args.saida).with_suffix('.json')
    saida_json.write_text(
        json.dumps([{'dados': r['dados'], 'score': r['score']} for r in resultados], indent=2, ensure_ascii=False),
        encoding='utf-8'
    )
    print(f"✅ Dados brutos salvos em: {saida_json}")


if __name__ == '__main__':
    main()
