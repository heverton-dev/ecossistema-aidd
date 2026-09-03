#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PHASE 1: Pesquisador de Referências
aidd-project-generator v2.1

Pesquisa projetos similares em:
- GitHub (via API — real)
- HuggingFace (via API — real)
- Replit (NÃO IMPLEMENTADO — sem API oficial; stub retorna sempre
  lista vazia, nunca dado fictício. Ver PesquisadorReplit.buscar)

Executa 4 gates de validação (R1-R4)
Gera _phase_01_index.json com auditoria completa

Tokens: 0 (100% Python determinístico)
"""

import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, List, Any
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# =============================================================================
# CONSTANTS
# =============================================================================

GITHUB_API_BASE = "https://api.github.com"
HF_API_BASE = "https://huggingface.co/api"
REPLIT_BASE = "https://replit.com"

TIMEOUT_SEGUNDOS = 5
MAX_RESULTADOS_POR_FONTE = 10

# =============================================================================
# DATA STRUCTURES
# =============================================================================

class Referencia:
    """Estrutura de uma referência encontrada"""
    def __init__(self,
                 nome: str,
                 url: str,
                 fonte: str,
                 metadata: Dict[str, Any]):
        self.nome = nome
        self.url = url
        self.fonte = fonte  # "github" | "huggingface" | "replit"
        self.metadata = metadata
        self.data_coletada = datetime.now(timezone.utc).isoformat()

    def to_dict(self):
        return {
            'nome': self.nome,
            'url': self.url,
            'fonte': self.fonte,
            'data_coletada': self.data_coletada,
            'metadata': self.metadata
        }


class Insight:
    """Consolidação de padrão encontrado"""
    def __init__(self,
                 tipo: str,  # "stack" | "arquitetura" | "dependencia"
                 descricao: str,
                 frequencia: int,
                 fontes: List[str]):
        self.tipo = tipo
        self.descricao = descricao
        self.frequencia = frequencia
        self.fontes = fontes

    def to_dict(self):
        return {
            'tipo': self.tipo,
            'descricao': self.descricao,
            'frequencia': self.frequencia,
            'fontes': self.fontes
        }


# =============================================================================
# PESQUISADORES (0 tokens)
# =============================================================================

# Mapeamento PT→EN de termos comuns de domínio. O GitHub indexa
# majoritariamente repositórios com nome/descrição em inglês; sem esta
# tradução, ideias em português geram queries que não refletem a intenção
# e o gate R2 (atividade recente) falha por irrelevância dos resultados.
# Chaves sem acento (NFKD) para casar com a normalização aplicada abaixo.
TRADUCOES_PT_EN = {
    'rastreador': 'tracker',
    'rastreadores': 'tracker',
    'habito': 'habit',
    'habitos': 'habit',
    'linha': 'cli',
    'comando': 'cli',
    'comandos': 'cli',
    'persistencia': 'persistence',
    'diario': 'daily',
    'checkin': 'checkin',
    'streak': 'streak',
    'sqlite': 'sqlite',
    'progresso': 'progress',
    'listar': 'list',
    'adicionar': 'add',
    'marcar': 'mark',
    'calcular': 'calculate',
    'dias': 'days',
    'consecutivos': 'consecutive',
    'dependencia': 'dependency',
    'externa': 'external',
    'credencial': 'credential',
    'terceiros': 'third-party',
    'api': 'api',
    'cli': 'cli',
    'local': 'local',
}


class PesquisadorGitHub:
    """Pesquisa projetos similares no GitHub via API"""

    @staticmethod
    def buscar(ideia: str, max_resultados: int = 10) -> List[Referencia]:
        """Busca repositórios similares (mín 100 stars).

        Sem fallback para dados fictícios: se a API falhar ou não
        retornar 200, o resultado é lista vazia (Zero Alucinação —
        nunca apresentar dado inventado como se fosse real).
        """
        referencias = []

        try:
            import re
            import unicodedata
            # Normaliza acentos (NFKD) para casar com TRADUCOES_PT_EN
            ideia_norm = unicodedata.normalize('NFKD', ideia).encode('ASCII', 'ignore').decode('ASCII')
            palavras = re.findall(r'[a-zA-Z0-9_]+', ideia_norm) if ideia else ['sales', 'erp', 'crm']
            stopwords = {'de', 'da', 'do', 'das', 'dos', 'via', 'com', 'em', 'para', 'por', 'um', 'uma', 'e', 'a', 'o'}
            palavras_filtradas = [w for w in palavras if w.lower() not in stopwords]
            palavras_chave = palavras_filtradas[:5] if palavras_filtradas else palavras[:5]
            # Enriquece com traduções PT→EN (mantém o termo original + tradução).
            # GitHub limita queries OR a 6 termos (acima disso retorna HTTP 422),
            # então deduplica e corta em 6.
            palavras_enriquecidas = []
            for w in palavras_chave:
                w_lower = w.lower()
                if w_lower not in palavras_enriquecidas:
                    palavras_enriquecidas.append(w_lower)
                traducao = TRADUCOES_PT_EN.get(w_lower)
                if traducao and traducao.lower() not in palavras_enriquecidas:
                    palavras_enriquecidas.append(traducao)
            query = ' OR '.join(palavras_enriquecidas[:6])

            params = {
                'q': f"{query} stars:>=100",
                'sort': 'stars',
                'order': 'desc',
                'per_page': 30
            }

            resp = requests.get(
                f"{GITHUB_API_BASE}/search/repositories",
                params=params,
                timeout=TIMEOUT_SEGUNDOS,
                headers={'Accept': 'application/vnd.github.v3+json'}
            )

            if resp.status_code != 200:
                print(f"⚠️  GitHub API retornou HTTP {resp.status_code}, sem referências desta fonte")
                return referencias

            items = resp.json().get('items', [])

            from datetime import timedelta
            agora = datetime.now(timezone.utc)
            dias_90_atras = agora - timedelta(days=90)

            itens_ativos = []
            itens_outros = []
            for item in items:
                if item.get('stargazers_count', 0) >= 100:
                    pushed_str = item.get('pushed_at')
                    is_ativo = False
                    if pushed_str:
                        try:
                            pushed_dt = datetime.fromisoformat(pushed_str.replace('Z', '+00:00'))
                            if pushed_dt >= dias_90_atras:
                                is_ativo = True
                        except:
                            pass
                    if is_ativo:
                        itens_ativos.append(item)
                    else:
                        itens_outros.append(item)

            candidatos = (itens_ativos + itens_outros)[:max_resultados]

            for item in candidatos:
                metadata = {
                    'stars': item['stargazers_count'],
                    'forks': item['forks_count'],
                    'linguagens': item.get('language') or 'unknown',
                    'ultimo_commit': item.get('pushed_at'),
                    'licenca': item.get('license', {}).get('name') if isinstance(item.get('license'), dict) else None,
                    'descricao': (item.get('description') or '')[:200]
                }
                ref = Referencia(
                    nome=item['full_name'],
                    url=item['html_url'],
                    fonte='github',
                    metadata=metadata
                )
                referencias.append(ref)

        except Exception as e:
            print(f"⚠️  Erro buscando GitHub: {e}")

        return referencias


class PesquisadorHuggingFace:
    """Pesquisa modelos/datasets similares no HuggingFace"""

    @staticmethod
    def buscar(ideia: str, max_resultados: int = 10) -> List[Referencia]:
        """Busca modelos/datasets relevantes"""
        referencias = []

        try:
            import re
            import unicodedata
            ideia_norm = unicodedata.normalize('NFKD', ideia).encode('ASCII', 'ignore').decode('ASCII')
            palavras = re.findall(r'[a-zA-Z0-9_]+', ideia_norm) if ideia else ['tracker', 'cli']
            stopwords = {'de', 'da', 'do', 'das', 'dos', 'via', 'com', 'em', 'para', 'por', 'um', 'uma', 'e', 'a', 'o'}
            palavras_filtradas = [w for w in palavras if w.lower() not in stopwords]
            busca_hf = ' '.join(palavras_filtradas[:3]) if palavras_filtradas else 'cli'

            # HF tem busca via URL
            params = {
                'search': busca_hf,
                'sort': 'trending',
                'direction': '-1'
            }

            # Busca modelos
            resp = requests.get(
                f"{HF_API_BASE}/models",
                params=params,
                timeout=TIMEOUT_SEGUNDOS
            )
            resp.raise_for_status()
            data = resp.json() if isinstance(resp.json(), list) else []

            for item in data[:max_resultados]:
                if isinstance(item, dict):
                    metadata = {
                        'downloads': item.get('downloads', 0),
                        'likes': item.get('likes', 0),
                        'tags': item.get('tags', []),
                        'library_name': item.get('library_name')
                    }
                    ref = Referencia(
                        nome=item.get('modelId', 'unknown'),
                        url=f"https://huggingface.co/{item.get('modelId', '')}",
                        fonte='huggingface',
                        metadata=metadata
                    )
                    referencias.append(ref)

        except Exception as e:
            print(f"⚠️  Erro buscando HuggingFace: {e}")

        return referencias


class PesquisadorReplit:
    """Pesquisa projetos educacionais/prototipagem no Replit.

    NÃO IMPLEMENTADO: Replit não expõe API pública de busca. Retorna
    sempre lista vazia — nunca dado inventado (Zero Alucinação).
    Implementação real exigiria scraping (Playwright/Selenium) ou
    parceria com API interna, fora do escopo desta fase.
    """

    @staticmethod
    def buscar(ideia: str, max_resultados: int = 10) -> List[Referencia]:
        return []


# =============================================================================
# CONSOLIDAÇÃO DE INSIGHTS (0 tokens)
# =============================================================================

class ConsolidadorInsights:
    """Consolida padrões encontrados em múltiplas fontes"""

    @staticmethod
    def analisar_referencias(referencias: List[Referencia]) -> Dict[str, Any]:
        """Extrai insights dos metadados"""

        # Contar linguagens mais comuns
        linguagens_map = {}
        for ref in referencias:
            lang = ref.metadata.get('linguagens') or 'unknown'
            linguagens_map[lang] = linguagens_map.get(lang, 0) + 1

        # Contar dependências
        dependencias_map = {}

        # Arquiteturas detectadas (baseado em nome + descrição)
        arquiteturas = []

        # Compilar em insights
        insights = []

        # Top linguagens
        for lang, count in sorted(linguagens_map.items(), key=lambda x: -x[1])[:5]:
            if lang != 'unknown':
                insights.append(Insight(
                    tipo='stack_linguagem',
                    descricao=lang,
                    frequencia=count,
                    fontes=['github']
                ).to_dict())

        return {
            'total_insights': len(insights),
            'insights': insights,
            'linguagens_comuns': dict(sorted(linguagens_map.items(), key=lambda x: -x[1])[:3]),
            'densidade_media_commits': 0  # Calculado se houver data
        }


# =============================================================================
# GATES DE VALIDAÇÃO (R1-R4)
# =============================================================================

class Gate:
    """Estrutura de resultado de gate"""
    def __init__(self,
                 gate_id: str,
                 descricao: str,
                 passou: bool,
                 detalhes: str):
        self.gate_id = gate_id
        self.descricao = descricao
        self.passou = passou
        self.detalhes = detalhes

    def to_dict(self):
        return {
            'gate_id': self.gate_id,
            'descricao': self.descricao,
            'status': 'PASSOU' if self.passou else 'FALHOU',
            'detalhes': self.detalhes
        }


class ValidadorGates:
    """Executa 4 gates de validação da Fase 1"""

    @staticmethod
    def executar_todos(referencias: List[Referencia]) -> tuple[List[Gate], bool]:
        """Executa R1-R4 sequencialmente. Retorna: (resultados, todos_passaram)"""
        gates_resultado = []

        # Gate R1: URLs válidas (HTTP 200)
        gate_r1 = ValidadorGates._gate_r1_urls_validas(referencias)
        gates_resultado.append(gate_r1)

        # Gate R2: Atividade recente (commits últimos 90 dias)
        gate_r2 = ValidadorGates._gate_r2_atividade_recente(referencias)
        gates_resultado.append(gate_r2)

        # Gate R3: Estrutura válida (parse OK)
        gate_r3 = ValidadorGates._gate_r3_estrutura_valida(referencias)
        gates_resultado.append(gate_r3)

        # Gate R4: Quantidade mínima (≥5)
        gate_r4 = ValidadorGates._gate_r4_quantidade_minima(referencias)
        gates_resultado.append(gate_r4)

        todos_passaram = all(g.passou for g in gates_resultado)

        return gates_resultado, todos_passaram

    @staticmethod
    def _gate_r1_urls_validas(referencias: List[Referencia]) -> Gate:
        """R1: Todas as URLs retornam HTTP 200"""
        validas = 0
        total = len(referencias)

        for ref in referencias:
            try:
                resp = requests.head(ref.url, timeout=TIMEOUT_SEGUNDOS)
                if resp.status_code == 200:
                    validas += 1
            except:
                pass  # URL inválida

        passou = validas == total
        detalhes = f"{validas}/{total} URLs retornaram HTTP 200"

        return Gate('R1_urls_validas',
                   'Validar URLs retornam HTTP 200',
                   passou,
                   detalhes)

    @staticmethod
    def _gate_r2_atividade_recente(referencias: List[Referencia]) -> Gate:
        """R2: ≥90% dos repos têm commits nos últimos 90 dias"""
        from datetime import timedelta

        agora = datetime.now(timezone.utc)
        dias_90_atras = agora - timedelta(days=90)

        ativos = 0
        total_com_data = 0

        for ref in referencias:
            last_commit_str = ref.metadata.get('ultimo_commit')
            if last_commit_str:
                try:
                    last_commit = datetime.fromisoformat(last_commit_str.replace('Z', '+00:00'))
                    total_com_data += 1
                    if last_commit >= dias_90_atras:
                        ativos += 1
                except:
                    pass

        if total_com_data == 0:
            taxa = 0
        else:
            taxa = (ativos / total_com_data) * 100

        passou = taxa >= 90
        detalhes = f"{ativos}/{total_com_data} repos com commits últimos 90 dias ({taxa:.0f}%)"

        return Gate('R2_atividade_recente',
                   'Verificar atividade recente',
                   passou,
                   detalhes)

    @staticmethod
    def _gate_r3_estrutura_valida(referencias: List[Referencia]) -> Gate:
        """R3: 100% das estruturas GitHub são parsáveis (JSON válido)"""
        validas = 0
        total = len(referencias)

        for ref in referencias:
            try:
                # Tentar serializar metadata
                json.dumps(ref.metadata)
                validas += 1
            except:
                pass

        passou = validas == total
        detalhes = f"{validas}/{total} estruturas de metadados válidas"

        return Gate('R3_estrutura_valida',
                   'Validar estrutura de dados',
                   passou,
                   detalhes)

    @staticmethod
    def _gate_r4_quantidade_minima(referencias: List[Referencia]) -> Gate:
        """R4: Mínimo 5 referências encontradas"""
        total = len(referencias)
        passou = total >= 5
        detalhes = f"{total} referências encontradas (mínimo: 5)"

        return Gate('R4_quantidade_minima',
                   'Verificar quantidade mínima',
                   passou,
                   detalhes)


# =============================================================================
# GERAÇÃO DE INDEX JSON
# =============================================================================

class GeradorPhaseIndex:
    """Gera _phase_01_index.json com auditoria completa"""

    @staticmethod
    def gerar(ideia_projeto: str,
              referencias: List[Referencia],
              insights: Dict[str, Any],
              matriz_stacks: Dict[str, Any],
              gates: List[Gate],
              todos_gates_passaram: bool,
              tempo_execucao_segundos: float) -> Dict[str, Any]:
        """Gera estrutura completa do index. Todo hash/tamanho é medido do
        conteúdo real de cada saída — nenhum valor é estimado ou fixo."""

        timestamp_inicio = datetime.now(timezone.utc)
        timestamp_conclusao = timestamp_inicio

        refs_github_json = json.dumps([r.to_dict() for r in referencias if r.fonte == 'github'], sort_keys=True).encode('utf-8')
        refs_hf_json = json.dumps([r.to_dict() for r in referencias if r.fonte == 'huggingface'], sort_keys=True).encode('utf-8')
        insights_json = json.dumps(insights, sort_keys=True).encode('utf-8')
        matriz_json = json.dumps(matriz_stacks, sort_keys=True).encode('utf-8')

        # Checksum de integridade do conjunto completo desta execução
        checksum = hashlib.sha256(refs_github_json + refs_hf_json + insights_json + matriz_json).hexdigest()

        total_checks = len(gates)
        passou = sum(1 for g in gates if g.passou)
        falhou = total_checks - passou

        index = {
            'fase_id': 'phase_01_research',
            'versao': '2.1',
            'status': 'COMPLETO' if todos_gates_passaram else 'FALHOU',

            'timestamps': {
                'data_inicio': timestamp_inicio.isoformat(),
                'data_conclusao': timestamp_conclusao.isoformat(),
                'duracao_segundos': tempo_execucao_segundos
            },

            'tokens': {
                'consumidos': 0,
                'percentual_determinismo': '100%'
            },

            'processamento': {
                'total_itens_processados': len(referencias),
                'total_novo_processado': len(referencias),
                'total_reutilizado_cache': 0,
                'checksum_integridade': checksum,
                'hash_conteudo': checksum[:16]
            },

            'validacoes': {
                'total_checks': total_checks,
                'passou': passou,
                'falhou': falhou,
                'avisos': 0,
                'taxa_sucesso_percentual': round((passou / total_checks) * 100, 1) if total_checks else 0
            },

            'saidas_estruturadas': {
                'referencias_github': {
                    'arquivo': './_phase_cache/referencias_github.json',
                    'quantidade': len([r for r in referencias if r.fonte == 'github']),
                    'tamanho_bytes': len(refs_github_json),
                    'hash': hashlib.sha256(refs_github_json).hexdigest()[:16]
                },
                'referencias_huggingface': {
                    'arquivo': './_phase_cache/referencias_hf.json',
                    'quantidade': len([r for r in referencias if r.fonte == 'huggingface']),
                    'tamanho_bytes': len(refs_hf_json),
                    'hash': hashlib.sha256(refs_hf_json).hexdigest()[:16]
                },
                'insights_consolidados': {
                    'arquivo': './_phase_cache/insights_phase1.json',
                    'quantidade': insights['total_insights'],
                    'tamanho_bytes': len(insights_json),
                    'hash': hashlib.sha256(insights_json).hexdigest()[:16]
                },
                'matriz_stacks': {
                    'arquivo': './_phase_cache/matriz_stacks.json',
                    'quantidade': len(insights.get('linguagens_comuns', {})),
                    'tamanho_bytes': len(matriz_json),
                    'hash': hashlib.sha256(matriz_json).hexdigest()[:16]
                }
            },

            'gates_executados': [g.to_dict() for g in gates],

            'resume_info': {
                'proxima_fase': 'phase_02_analysis',
                'arquivos_temporarios': ['./_phase_cache/*'],
                'dependencias_satisfeitas': todos_gates_passaram,
                'pode_prosseguir': todos_gates_passaram,
                'requer_intervencao_manual': not todos_gates_passaram
            },

            'metadados': {
                'criado_por': 'aidd-project-generator v2.1',
                'ideia_projeto': ideia_projeto,
                'projeto_hash': hashlib.md5(ideia_projeto.encode()).hexdigest()[:8],
                'ambiente': {
                    'sistema_operacional': sys.platform,
                    'versao_python': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
                }
            }
        }

        return index


# =============================================================================
# ORQUESTRADOR PRINCIPAL
# =============================================================================

class PesquisadorFase1:
    """Orquestrador da Fase 1: Pesquisa de Referências"""

    def __init__(self, pasta_cache: Path):
        self.pasta_cache = Path(pasta_cache)
        self.pasta_data = self.pasta_cache / 'data'
        self.pasta_data.mkdir(parents=True, exist_ok=True)

    def executar(self, ideia_projeto: str) -> Optional[Dict[str, Any]]:
        """Executa pipeline completo da Fase 1"""
        print(f"\n🔍 PHASE 1: Pesquisador de Referências")
        print(f"   Ideia: {ideia_projeto}")
        print(f"   {'-' * 60}")

        tempo_inicio = datetime.now()

        # 1. Pesquisar em paralelo (3 fontes)
        print(f"\n📊 Buscando referências...")
        referencias = self._buscar_referencias_paralelo(ideia_projeto)
        print(f"   ✓ Total encontrado: {len(referencias)} referências")

        # 2. Consolidar insights
        print(f"\n🔗 Consolidando insights...")
        insights = ConsolidadorInsights.analisar_referencias(referencias)
        print(f"   ✓ {insights['total_insights']} insights extraídos")

        # 3. Executar gates
        print(f"\n✅ Executando gates (R1-R4)...")
        gates, todos_passaram = ValidadorGates.executar_todos(referencias)
        for gate in gates:
            status_icon = "✓" if gate.passou else "✗"
            print(f"   {status_icon} {gate.gate_id}: {gate.detalhes}")

        if not todos_passaram:
            print(f"\n❌ FASE FALHOU: Gates não passaram")
            return None

        # 4. Gerar index
        tempo_execucao = (datetime.now() - tempo_inicio).total_seconds()
        print(f"\n📝 Gerando índice de fase...")
        matriz_stacks = self._montar_matriz_stacks(referencias, insights)
        index = GeradorPhaseIndex.gerar(
            ideia_projeto,
            referencias,
            insights,
            matriz_stacks,
            gates,
            todos_passaram,
            tempo_execucao
        )

        # 5. Salvar cache estruturado
        print(f"\n💾 Salvando cache estruturado...")
        self._salvar_cache(referencias, insights, matriz_stacks)

        # 6. Salvar index
        path_index = self.pasta_cache / '_phase_01_index.json'
        with open(path_index, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2, ensure_ascii=False)
        print(f"   ✓ {path_index}")

        print(f"\n{'=' * 60}")
        print(f"✅ PHASE 1 COMPLETO")
        print(f"   Status: {index['status']}")
        print(f"   Tempo: {tempo_execucao:.1f}s")
        print(f"   Tokens: {index['tokens']['consumidos']} (100% determinístico, zero chamada LLM)")
        print(f"{'=' * 60}\n")

        return index

    def _buscar_referencias_paralelo(self, ideia: str) -> List[Referencia]:
        """Executa 3 pesquisas em paralelo"""
        referencias = []

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(PesquisadorGitHub.buscar, ideia): 'github',
                executor.submit(PesquisadorHuggingFace.buscar, ideia): 'huggingface',
                executor.submit(PesquisadorReplit.buscar, ideia): 'replit',
            }

            for future in as_completed(futures):
                fonte = futures[future]
                try:
                    resultado = future.result()
                    referencias.extend(resultado)
                    print(f"   ✓ {fonte}: {len(resultado)} encontrados")
                except Exception as e:
                    print(f"   ⚠️  {fonte}: erro ({e})")

        return referencias

    @staticmethod
    def _montar_matriz_stacks(referencias: List[Referencia], insights: Dict[str, Any]) -> Dict[str, Any]:
        """Monta a matriz de stacks a partir de dados reais já coletados"""
        return {
            'linguagens_comuns': insights.get('linguagens_comuns', {}),
            'total_referencias': len(referencias),
            'fontes': sorted(set(r.fonte for r in referencias))
        }

    def _salvar_cache(self, referencias: List[Referencia],
                     insights: Dict[str, Any],
                     matriz_stacks: Dict[str, Any]):
        """Salva outputs estruturados para próxima fase"""

        # Separar por fonte
        refs_github = [r.to_dict() for r in referencias if r.fonte == 'github']
        refs_hf = [r.to_dict() for r in referencias if r.fonte == 'huggingface']

        # Salvar JSONs
        (self.pasta_data / 'referencias_github.json').write_text(
            json.dumps(refs_github, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )
        (self.pasta_data / 'referencias_hf.json').write_text(
            json.dumps(refs_hf, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )
        (self.pasta_data / 'insights_phase1.json').write_text(
            json.dumps(insights, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )
        (self.pasta_data / 'matriz_stacks.json').write_text(
            json.dumps(matriz_stacks, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )


# =============================================================================
# ENTRY POINT
# =============================================================================

def main():
    """CLI para testar Phase 1"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Phase 1: Pesquisador de Referências - aidd-project-generator v2.1'
    )
    parser.add_argument('ideia',
                       help='Descrição breve da ideia do projeto')
    parser.add_argument('--cache-dir',
                       default='.aidd/cache',
                       help='Diretório para cache (padrão: .aidd/cache)')

    args = parser.parse_args()

    pesquisador = PesquisadorFase1(Path(args.cache_dir))
    resultado = pesquisador.executar(args.ideia)

    if resultado is None:
        sys.exit(1)

    sys.exit(0)


if __name__ == '__main__':
    main()
