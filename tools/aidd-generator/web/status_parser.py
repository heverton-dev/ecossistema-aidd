#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Parser de Status das Fases e Resultados
web/status_parser.py — aidd-project-generator
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Definição canônica das fases do pipeline
FASES_CANONICAS = [
    {
        'numero': 1,
        'chave': 'fase_1',
        'arquivo_index': '_phase_01_index.json',
        'nome': 'Fase 1 — Pesquisador',
        'subtitulo': 'Pesquisa referências e padrões de arquitetura',
        'obrigatoria': True
    },
    {
        'numero': 2,
        'chave': 'fase_2',
        'arquivo_index': '_phase_02_index.json',
        'nome': 'Fase 2 — Analisador',
        'subtitulo': 'Análise de viabilidade e restrições com IA',
        'obrigatoria': True
    },
    {
        'numero': 3,
        'chave': 'fase_3',
        'arquivo_index': '_phase_03_index.json',
        'nome': 'Fase 3 — Designer',
        'subtitulo': 'Geração da arquitetura técnica em 5 subagentes',
        'obrigatoria': True
    },
    {
        'numero': 4,
        'chave': 'fase_4',
        'arquivo_index': '_phase_04_index.json',
        'nome': 'Fase 4 — Decisor',
        'subtitulo': 'Decisão e validação das configurações do projeto',
        'obrigatoria': True
    },
    {
        'numero': 5,
        'chave': 'fase_5',
        'arquivo_index': '_phase_05_index.json',
        'nome': 'Fase 5 — Criador',
        'subtitulo': 'Criação mecânica da árvore de arquivos e estrutura',
        'obrigatoria': True
    },
    {
        'numero': 8,
        'chave': 'fase_8',
        'arquivo_index': '_phase_08_index.json',
        'nome': 'Fase 8 — Implementador Funcional',
        'subtitulo': 'Implementação de código Python real e testes unitários',
        'obrigatoria': False  # Apenas quando --implementar-codigo é usado
    },
    {
        'numero': 6,
        'chave': 'fase_6',
        'arquivo_index': '_phase_06_index.json',
        'nome': 'Fase 6 — Documentador',
        'subtitulo': 'Geração de documentação completa (HTML, PDF, Markdown)',
        'obrigatoria': True
    },
    {
        'numero': 7,
        'chave': 'fase_7',
        'arquivo_index': '_phase_07_index.json',
        'nome': 'Fase 7 — Auto-crítica',
        'subtitulo': 'Auditoria de qualidade, cálculo de score e roadmap',
        'obrigatoria': True
    }
]


def obter_sequencia_fases(implementar_codigo: bool = False) -> List[Dict[str, Any]]:
    """Retorna a lista ordenada de fases conforme a flag de implementação de código."""
    if implementar_codigo:
        # Ordem com --implementar-codigo: 1→2→3→4→5→8→6→7
        return [f for f in FASES_CANONICAS]
    else:
        # Ordem padrão: 1→2→3→4→5→6→7
        return [f for f in FASES_CANONICAS if f['numero'] != 8]


def ler_json_seguro(caminho: Path) -> Optional[Dict[str, Any]]:
    """Lê um arquivo JSON de forma segura com tratamento de erros."""
    if not caminho.exists():
        return None
    try:
        conteudo = caminho.read_text(encoding='utf-8')
        if not conteudo.strip():
            return None
        return json.loads(conteudo)
    except Exception:
        return None


def extrair_gates_de_index(dados: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extrai lista de gates com status e descrições."""
    gates_res: List[Dict[str, Any]] = []
    if not isinstance(dados, dict):
        return gates_res

    gates_raw = dados.get('gates') or dados.get('qualidade', {}).get('gates', [])
    if isinstance(gates_raw, list):
        for g in gates_raw:
            if isinstance(g, dict):
                gates_res.append({
                    'id': g.get('id') or g.get('codigo', 'GATE'),
                    'descricao': g.get('descricao', ''),
                    'passou': bool(g.get('passou', False)),
                    'severidade': g.get('severidade', 'CRITICA'),
                    'mensagem': g.get('mensagem', '')
                })
    return gates_res


def analisar_status_pasta_projeto(
    pasta_projeto: Path,
    implementar_codigo: bool = False,
    fase_atual_subprocess: Optional[str] = None,
    subprocess_rodando: bool = False
) -> Dict[str, Any]:
    """
    Inspeciona a pasta do projeto e o diretório .aidd/cache/ para construir
    o checklist de status ao vivo de cada fase.
    """
    pasta_projeto = Path(pasta_projeto)
    cache_dir = pasta_projeto / '.aidd' / 'cache'
    fases_definidas = obter_sequencia_fases(implementar_codigo)

    fases_status: List[Dict[str, Any]] = []
    total_tokens = 0
    tempo_total = 0.0
    fases_concluidas_count = 0
    todos_gates: List[Dict[str, Any]] = []
    dados_fase_8: Optional[Dict[str, Any]] = None
    dados_fase_7: Optional[Dict[str, Any]] = None

    encontrou_fase_em_andamento = False

    for idx, fase_def in enumerate(fases_definidas):
        chave = fase_def['chave']
        arquivo_index = cache_dir / fase_def['arquivo_index']
        dados_index = ler_json_seguro(arquivo_index)

        status = 'pendente'
        duracao = 0.0
        tokens = 0
        gates_fase: List[Dict[str, Any]] = []

        if dados_index:
            # Fase concluída no disco
            status_index = dados_index.get('status', '').upper()
            if status_index == 'COMPLETO' or dados_index.get('sucesso') is True or dados_index.get('projeto_pronto') is True:
                status = 'concluida'
                fases_concluidas_count += 1
            elif status_index == 'FALHOU':
                status = 'falhou'
            else:
                status = 'concluida'
                fases_concluidas_count += 1

            # Extração de métricas de tempo
            timestamps = dados_index.get('timestamps', {})
            duracao = float(timestamps.get('duracao_segundos') or dados_index.get('duracao_segundos', 0.0))
            tempo_total += duracao

            # Extração de tokens consumidos reais
            tokens_obj = dados_index.get('tokens', {})
            if isinstance(tokens_obj, dict):
                tokens_consumidos = tokens_obj.get('consumidos')
                if isinstance(tokens_consumidos, (int, float)):
                    tokens = int(tokens_consumidos)
                    total_tokens += tokens

            # Gates da fase
            gates_fase = extrair_gates_de_index(dados_index)
            todos_gates.extend(gates_fase)

            if fase_def['numero'] == 8:
                dados_fase_8 = dados_index
            elif fase_def['numero'] == 7:
                dados_fase_7 = dados_index

        elif subprocess_rodando and not encontrou_fase_em_andamento:
            # Se ainda não concluiu e o subprocess está rodando:
            # A primeira fase que não possui index no disco é a fase atual 'rodando'
            status = 'rodando'
            encontrou_fase_em_andamento = True

        fases_status.append({
            'numero': fase_def['numero'],
            'chave': chave,
            'nome': fase_def['nome'],
            'subtitulo': fase_def['subtitulo'],
            'status': status,
            'duracao_segundos': duracao,
            'tokens_consumidos': tokens,
            'gates': gates_fase
        })

    # Resumo de testes se Fase 8 rodou
    resumo_testes = None
    if dados_fase_8:
        py_res = dados_fase_8.get('resultado_pytest') or {}
        if py_res:
            resumo_testes = {
                'coletados': py_res.get('coletados', 0),
                'passaram': py_res.get('passaram', 0),
                'falharam': py_res.get('falharam', 0),
                'duracao': py_res.get('duracao_segundos', 0.0),
                'todos_passaram': py_res.get('passaram', 0) > 0 and py_res.get('falharam', 0) == 0
            }

    # Resumo de score se Fase 7 rodou
    score_final = None
    resumo_autocritica = None
    if dados_fase_7:
        score_final = dados_fase_7.get('score')
        resumo_autocritica = {
            'score': score_final,
            'pontos_fortes': dados_fase_7.get('pontos_fortes', []),
            'pontos_fracos': dados_fase_7.get('pontos_fracos', []),
            'roadmap': dados_fase_7.get('roadmap', []),
            'investimento': dados_fase_7.get('investimento', {})
        }

    total_fases = len(fases_definidas)
    progresso_percentual = int((fases_concluidas_count / total_fases) * 100) if total_fases > 0 else 0

    return {
        'total_fases': total_fases,
        'fases_concluidas': fases_concluidas_count,
        'progresso_percentual': progresso_percentual,
        'fases': fases_status,
        'tempo_total_segundos': tempo_total,
        'tokens_totais_consumidos': total_tokens,
        'gates_totais': todos_gates,
        'gates_passaram': sum(1 for g in todos_gates if g['passou']),
        'gates_falharam': sum(1 for g in todos_gates if not g['passou']),
        'resultado_testes': resumo_testes,
        'score_final': score_final,
        'autocritica': resumo_autocritica,
        'pasta_existe': pasta_projeto.exists()
    }
