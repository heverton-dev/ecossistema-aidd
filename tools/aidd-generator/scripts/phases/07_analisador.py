#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PHASE 7: Analisador Crítico Automático
aidd-project-generator v2.1+

Fase NOVA (v0 de transcendência):
Analisa o sistema automaticamente após geração de projeto.

Lei Fundamental: O projeto se auto-avalia. Honestidade total.

Tokens: 0k (Python puro — avaliação é determinística)
Determinismo: 100% (sem LLM, apenas análise)
"""

import sys
import os
import re
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, List, Any

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# =============================================================================
# MAPA ESTRUTURAL DE SEÇÕES (HANDOFF FASE 6 -> FASE 7)
# =============================================================================

TOPICOS_CHAVE_MAPA = {
    'requisitos': [r'\brequisitos?\b', r'\brequirements?\b'],
    'arquitetura': [r'\barquiteturas?\b', r'\barchitectures?\b', r'\barquitetural\b'],
    'testes': [r'\btestes?\b', r'\btests?\b', r'\btestagem\b', r'\btesting\b'],
}


def _extrair_resumo_executivo(texto: str, max_frases: int = 3) -> str:
    """Extrai 2-3 frases semânticas do documento para compor o resumo executivo."""
    texto_limpo = re.sub(r'```[\s\S]*?```', ' ', texto)
    texto_limpo = re.sub(r'<style[\s\S]*?</style>', ' ', texto_limpo, flags=re.IGNORECASE)
    texto_limpo = re.sub(r'<script[\s\S]*?</script>', ' ', texto_limpo, flags=re.IGNORECASE)
    texto_limpo = re.sub(r'<[^>]+>', ' ', texto_limpo)

    linhas_validas = []
    for linha in texto_limpo.splitlines():
        l = linha.strip()
        if not l or l.startswith(('#', '*', '-', '|', '>', '=', '~')):
            continue
        linhas_validas.append(l)

    texto_corrido = ' '.join(linhas_validas)
    if not texto_corrido:
        return "Documento sem conteúdo textual descritivo suficiente para resumo."

    candidatos = [
        f.strip() for f in re.split(r'(?<=[.!?])\s+', texto_corrido)
        if len(f.strip()) >= 15
    ]
    frases = candidatos[:max_frases]
    if not frases:
        frases = [texto_corrido[:150].strip() + '...']
    return ' '.join(frases)


def _detectar_topicos_chave(texto: str) -> List[str]:
    """Detecta presença dos tópicos-chave (requisitos, arquitetura, testes)."""
    encontrados = []
    for topico, regexes in TOPICOS_CHAVE_MAPA.items():
        if any(re.search(rx, texto, re.IGNORECASE) for rx in regexes):
            encontrados.append(topico)
    return encontrados


def montar_mapa_secoes(artefatos: Dict) -> str:
    """Extrai título da seção, número de linhas, tópicos-chave e resumo executivo de 2-3 frases por documento.

    Substitui o repasse e carregamento de HTML/MD integral pelo mapa de seções resumido,
    garantindo redução de >= 50% dos tokens de handoff da Fase 6 para a Fase 7.
    """
    if not artefatos:
        return ""

    linhas_mapa = [
        "# MAPA ESTRUTURAL DE SEÇÕES (HANDOFF FASE 6 -> FASE 7)",
        "",
    ]

    for nome_doc, dado in sorted(artefatos.items(), key=lambda x: str(x[0])):
        if isinstance(dado, Path):
            conteudo = dado.read_text(encoding='utf-8', errors='ignore') if dado.exists() else ""
        elif isinstance(dado, dict):
            conteudo = dado.get('conteudo') or dado.get('content') or ""
            if not conteudo and 'path' in dado:
                p = Path(dado['path'])
                conteudo = p.read_text(encoding='utf-8', errors='ignore') if p.exists() else ""
        elif isinstance(dado, str):
            p = Path(dado)
            if p.exists() and p.is_file():
                try:
                    conteudo = p.read_text(encoding='utf-8', errors='ignore')
                except Exception:
                    conteudo = dado
            else:
                conteudo = dado
        else:
            conteudo = str(dado)

        linhas_doc = conteudo.splitlines()
        total_linhas = len(linhas_doc)

        topicos = _detectar_topicos_chave(conteudo)
        resumo = _extrair_resumo_executivo(conteudo, max_frases=3)

        secoes = []
        secao_atual = "Início"
        linhas_secao = 0

        for linha in linhas_doc:
            match_md = re.match(r'^(#{1,6})\s+(.+)$', linha.strip())
            match_html = re.search(r'<h[1-6][^>]*>(.*?)</h[1-6]>', linha, re.IGNORECASE)

            novo_titulo = None
            if match_md:
                novo_titulo = match_md.group(2).strip()
            elif match_html:
                novo_titulo = re.sub(r'<[^>]+>', '', match_html.group(1)).strip()

            if novo_titulo:
                if linhas_secao > 0 or secao_atual != "Início":
                    secoes.append((secao_atual, linhas_secao))
                secao_atual = novo_titulo
                linhas_secao = 1
            else:
                linhas_secao += 1

        if linhas_secao > 0:
            secoes.append((secao_atual, linhas_secao))

        linhas_mapa.append(f"## Documento: {nome_doc}")
        linhas_mapa.append(f"- **Total de Linhas:** {total_linhas}")
        linhas_mapa.append(f"- **Tópicos-Chave:** {', '.join(topicos) if topicos else 'nenhum'}")
        linhas_mapa.append(f"- **Resumo Executivo:** {resumo}")
        linhas_mapa.append("- **Seções:**")
        for tit, n_lin in secoes[:25]:
            topicos_sec = _detectar_topicos_chave(tit)
            sufixo = f" (tópicos: {', '.join(topicos_sec)})" if topicos_sec else ""
            linhas_mapa.append(f"  - `{tit}`: ~{n_lin} linhas{sufixo}")
        if len(secoes) > 25:
            linhas_mapa.append(f"  - ... ({len(secoes) - 25} seções adicionais condensadas)")
        linhas_mapa.append("")

    return "\n".join(linhas_mapa).strip()


# =============================================================================
# ANALISADOR CRÍTICO
# =============================================================================

class AnalisadorCriticoAutomatico:
    """Análise crítica automática do sistema"""

    def __init__(self, pasta_projeto: Path):
        self.pasta_projeto = Path(pasta_projeto)
        self.cache_path = self.pasta_projeto / '.aidd' / 'cache'
        self.mapa_secoes = ""

    def executar(self, artefatos: Optional[Dict] = None) -> Dict:
        """Executar análise crítica completa"""
        print(f"\n📊 PHASE 7: Analisador Crítico Automático")
        print(f"   Projeto: {self.pasta_projeto.name}")
        print(f"   {'-' * 60}")

        tempo_inicio = datetime.now()

        # 1. Coletar dados de todas as phases e estruturar mapa de seções (substitui dump HTML/MD integral)
        print(f"\n🔍 Coletando dados das phases e montando mapa de seções...")
        dados = self._coletar_dados_phases()
        artefatos_alvo = artefatos if artefatos is not None else self._coletar_artefatos_fase6(dados)
        mapa_secoes = montar_mapa_secoes(artefatos_alvo) if artefatos_alvo else ""
        self.mapa_secoes = mapa_secoes
        print(f"   ✓ Dados coletados (mapa estruturado: {len(mapa_secoes.splitlines())} linhas)")

        # 2. Calcular score
        print(f"\n📈 Calculando score do projeto...")
        score = self._calcular_score(dados)
        print(f"   ✓ Score: {score['total']}/100")

        # 3. Listar pontos fortes
        print(f"\n✅ Identificando pontos fortes...")
        pontos_fortes = self._identificar_pontos_fortes(dados)
        print(f"   ✓ {len(pontos_fortes)} pontos fortes")

        # 4. Listar pontos fracos
        print(f"\n⚠️  Identificando pontos fracos...")
        pontos_fracos = self._identificar_pontos_fracos(dados)
        print(f"   ✓ {len(pontos_fracos)} pontos a melhorar")

        # 5. Listar requisitos críticos
        print(f"\n🔴 Listando requisitos críticos...")
        requisitos = self._listar_requisitos_criticos(dados)
        print(f"   ✓ {len(requisitos)} requisitos identificados")

        # 6. Gerar roadmap
        print(f"\n🚀 Gerando roadmap personalizado...")
        roadmap = self._gerar_roadmap(score)
        print(f"   ✓ Roadmap com {len(roadmap['fases'])} fases")

        # 7. Calcular investimento
        print(f"\n💰 Calculando investimento necessário...")
        investimento = self._calcular_investimento(roadmap)
        print(f"   ✓ {investimento['total_horas']}h, ${investimento['custo_total']}k")

        # 8. Consolidar tokens por origem de medição (transparência de métricas)
        tokens_consolidado = self._consolidar_tokens_por_origem(dados)

        # 9. Gerar relatório markdown
        print(f"\n📄 Gerando relatório markdown...")
        relatorio = self._gerar_relatorio_markdown({
            'score': score,
            'pontos_fortes': pontos_fortes,
            'pontos_fracos': pontos_fracos,
            'requisitos': requisitos,
            'roadmap': roadmap,
            'investimento': investimento,
            'tokens_consolidado': tokens_consolidado,
            'mapa_secoes': mapa_secoes,
        })

        # 10. Salvar artefatos
        print(f"\n💾 Salvando artefatos...")
        self._salvar_artefatos({
            'relatorio': relatorio,
            'score': score,
            'roadmap': roadmap,
            'pontos_fortes': pontos_fortes,
            'pontos_fracos': pontos_fracos,
            'tokens_consolidado': tokens_consolidado,
            'mapa_secoes': mapa_secoes,
        })
        print(f"   ✓ AVALIACAO-AUTO-CRITICA.md")
        print(f"   ✓ .aidd/ROADMAP-EVOLUCAO.md")
        print(f"   ✓ .aidd/cache/_phase_07_index.json")

        tempo_execucao = (datetime.now() - tempo_inicio).total_seconds()

        print(f"\n{'=' * 60}")
        print(f"✅ PHASE 7 COMPLETO — AUTO-CRÍTICA REALIZADA")
        print(f"   Score: {score['total']}/100")
        print(f"   Status: {score['classificacao']}")
        print(f"   Tokens: {tokens_consolidado['consolidado_texto']}")
        print(f"   Roadmap: {len(roadmap['fases'])} fases até 100/100")
        print(f"   Tempo: {tempo_execucao:.1f}s")
        print(f"{'=' * 60}\n")

        return {
            'status': 'COMPLETO',
            'score': score['total'],
            'tempo_execucao': tempo_execucao,
            'tokens_consolidado': tokens_consolidado,
            'mapa_secoes': mapa_secoes,
            'artefatos': ['AVALIACAO-AUTO-CRITICA.md', '.aidd/ROADMAP-EVOLUCAO.md']
        }

    def _coletar_artefatos_fase6(self, dados: Dict) -> Dict[str, str]:
        """Localiza artefatos gerados pela Fase 6 (HTML/MD) para montagem do mapa de seções."""
        artefatos = {}
        phase6 = dados.get('phase_6', {})
        arquivos = phase6.get('processamento', {}).get('arquivos', {})
        for formato, caminho in arquivos.items():
            if formato in ('html', 'md'):
                p = Path(caminho)
                if not p.is_absolute():
                    p = self.pasta_projeto / p
                if p.exists() and p.is_file():
                    try:
                        artefatos[p.name] = p.read_text(encoding='utf-8', errors='ignore')
                    except Exception:
                        pass
        if not artefatos:
            output_dir = self.pasta_projeto / 'output'
            if output_dir.exists():
                for ext in ('*.md', '*.html'):
                    for f in output_dir.rglob(ext):
                        if f.is_file():
                            try:
                                artefatos[f.name] = f.read_text(encoding='utf-8', errors='ignore')
                            except Exception:
                                pass
        return artefatos

    def _coletar_dados_phases(self) -> Dict:
        """Coletar dados de _phase_*.json (fases 1-7, e 8 se existir)"""
        dados = {}

        for i in range(1, 9):
            index_file = self.cache_path / f'_phase_{i:02d}_index.json'
            if index_file.exists():
                with open(index_file, 'r', encoding='utf-8') as f:
                    dados[f'phase_{i}'] = json.load(f)

        return dados

    @staticmethod
    def _dim_completude_pipeline(dados: Dict, tem_fase8: bool, total_fases: int) -> int:
        """Dimensão 1: quantas phases completaram (de 6, ou de 7 se phase_8 existe)."""
        phases_completas = sum(
            1 for i in range(1, 8 if tem_fase8 else 7)
            if dados.get(f'phase_{i}', {}).get('status') == 'COMPLETO'
        )
        return int((phases_completas / total_fases) * 100)

    @staticmethod
    def _dim_qualidade_gates(dados: Dict, tem_fase8: bool) -> int:
        """Dimensão 2: gate pass rate — total que passou / total executado (inclui phase_8 se existir)."""
        total_gates = 0
        gates_passaram = 0
        for i in range(1, 9 if tem_fase8 else 7):
            phase = dados.get(f'phase_{i}', {})
            for gate in phase.get('gates_executados', []):
                total_gates += 1
                if gate.get('status') == 'PASSOU':
                    gates_passaram += 1
        return int((gates_passaram / max(total_gates, 1)) * 100)

    @staticmethod
    def _dim_determinismo(dados: Dict) -> int:
        """Dimensão 3: média do percentual_determinismo das phases 1-6."""
        determinismos = []
        for i in range(1, 7):
            phase = dados.get(f'phase_{i}', {})
            det = phase.get('tokens', {}).get('percentual_determinismo', 0)
            if isinstance(det, str):
                det = int(det.replace('%', ''))
            determinismos.append(det)
        avg_det = sum(determinismos) / max(len(determinismos), 1) if determinismos else 0
        return int(min(avg_det, 100))

    @staticmethod
    def _dim_validacoes(dados: Dict) -> int:
        """Dimensão 4: taxa de sucesso das validações (de phase_1 se disponível)."""
        validacoes = dados.get('phase_1', {}).get('validacoes', {})
        if not validacoes:
            return 50  # sem dados → neutro
        passou = validacoes.get('passou', 0)
        total = validacoes.get('total_checks', max(passou, 1))
        return int(min((passou / max(total, 1)) * 100, 100))

    @staticmethod
    def _dim_documentacao(dados: Dict) -> int:
        """Dimensão 6: phase_6 completa e com formatos."""
        phase6 = dados.get('phase_6', {})
        if phase6.get('status') != 'COMPLETO':
            return 0
        formatos = phase6.get('processamento', {}).get('formatos', [])
        return min(60 + len(formatos) * 15, 100)

    @staticmethod
    def _dim_rastreabilidade(dados: Dict, tem_fase8: bool, total_fases: int) -> int:
        """Dimensão 7: phases com gates definidos (1-7; inclui 8 se existir)."""
        phases_com_gates = sum(
            1 for i in range(1, 9 if tem_fase8 else 7)
            if dados.get(f'phase_{i}', {}).get('gates_executados')
        )
        return int(min((phases_com_gates / total_fases) * 100, 100))

    @staticmethod
    def _classificar_score(base_score: int) -> str:
        """Traduz o score total (1-100) na classificação textual correspondente."""
        classificacoes = {
            10: "Começando",
            25: "Básico",
            50: "Prototipo",
            60: "Funcional",
            75: "Robusto",
            85: "Profissional",
            100: "TRANSCENDENTE",
        }
        classificacao = "Começando"
        for threshold, label in sorted(classificacoes.items()):
            if base_score >= threshold:
                classificacao = label
        return classificacao

    def _calcular_score(self, dados: Dict) -> Dict:
        """Calcular score do projeto (1-100) a partir de métricas reais.

        Quando phase_8 existe nos dados (pipeline com --implementar-codigo),
        a completude considera 7 fases e os gates da fase 8 são incluídos
        na avaliação de qualidade. Dimensões 3-7 permanecem baseadas em
        fases 1-7 (determinismo, validações, docs, rastreabilidade).
        """
        tem_fase8 = 'phase_8' in dados
        total_fases = 7 if tem_fase8 else 6

        dimensoes = {
            'completude_pipeline': self._dim_completude_pipeline(dados, tem_fase8, total_fases),
            'qualidade_gates': self._dim_qualidade_gates(dados, tem_fase8),
            'determinismo': self._dim_determinismo(dados),
            'validacoes': self._dim_validacoes(dados),
            'documentacao': self._dim_documentacao(dados),
            'rastreabilidade': self._dim_rastreabilidade(dados, tem_fase8, total_fases),
        }

        # Score total: média ponderada
        # Nota: não há dimensão "economia de tokens vs abordagem ingênua" —
        # medir isso exigiria rodar a mesma tarefa via LLM puro como baseline
        # comparativo, o que não é feito. 'determinismo' já mede honestamente
        # a mesma intenção (Python determinístico vs LLM) com dado real
        # (percentual_determinismo reportado por cada fase).
        pesos = {
            'completude_pipeline': 20,
            'qualidade_gates': 20,
            'determinismo': 25,
            'validacoes': 10,
            'documentacao': 15,
            'rastreabilidade': 10,
        }
        total_ponderado = sum(
            dimensoes[d] * pesos[d] for d in dimensoes
        )
        base_score = int(total_ponderado / sum(pesos.values()))

        # Garantir range 1-100
        base_score = max(1, min(base_score, 100))

        return {
            'total': base_score,
            'por_dimensao': dimensoes,
            'classificacao': self._classificar_score(base_score),
        }

    def _identificar_pontos_fortes(self, dados: Dict) -> List[str]:
        """Detectar pontos fortes a partir de dados reais"""
        fortes = []
        tem_fase8 = 'phase_8' in dados

        # 1. Pipeline completo (fases 1-6; inclui 7 e 8 na contagem se existirem)
        phases_completas = [
            i for i in range(1, 7)
            if dados.get(f'phase_{i}', {}).get('status') == 'COMPLETO'
        ]
        total_base = 7 if tem_fase8 else 6
        if dados.get('phase_7', {}).get('status') == 'COMPLETO':
            phases_completas.append(7)
        if tem_fase8 and dados.get('phase_8', {}).get('status') == 'COMPLETO':
            phases_completas.append(8)
        if len(phases_completas) >= total_base - 1:
            fortes.append(f"✅ Pipeline completo ({len(phases_completas)}/{total_base} phases)")
        elif len(phases_completas) >= 3:
            fortes.append(f"✅ Pipeline parcial ({len(phases_completas)}/{total_base} phases)")

        # 2. Gates 100% passando (inclui phase_8 se existir)
        total_gates = 0
        gates_passaram = 0
        for i in range(1, 9 if tem_fase8 else 7):
            for gate in dados.get(f'phase_{i}', {}).get('gates_executados', []):
                total_gates += 1
                if gate.get('status') == 'PASSOU':
                    gates_passaram += 1
        if total_gates > 0 and gates_passaram == total_gates:
            fortes.append(f"✅ {total_gates} gates mecânicos — 100% passando")
        elif total_gates > 0:
            taxa = int((gates_passaram / total_gates) * 100)
            if taxa >= 80:
                fortes.append(f"✅ {gates_passaram}/{total_gates} gates passando ({taxa}%)")

        # 3. Alto determinismo (fases 1-6; phase 8 é 0% por natureza LLM)
        for i in range(1, 7):
            phase = dados.get(f'phase_{i}', {})
            det = phase.get('tokens', {}).get('percentual_determinismo', 0)
            if isinstance(det, str):
                det = int(det.replace('%', ''))
            if det >= 90:
                fortes.append(f"✅ Phase {i} com determinismo {det}%")
                break  # reportar apenas a melhor

        # 5. Validações sem falhas
        validacoes = dados.get('phase_1', {}).get('validacoes', {})
        if validacoes and validacoes.get('falhou', 0) == 0:
            total_v = validacoes.get('total_checks', 0)
            if total_v > 0:
                fortes.append(f"✅ {total_v} validações sem falhas")

        # 6. Documentação gerada em múltiplos formatos
        phase6 = dados.get('phase_6', {})
        formatos = phase6.get('processamento', {}).get('formatos', [])
        if len(formatos) >= 3:
            fortes.append(f"✅ Documentação em {len(formatos)} formatos ({', '.join(formatos)})")

        # 7. Zero alucinação (gate A2 se existir)
        for i in range(1, 9 if tem_fase8 else 7):
            for gate in dados.get(f'phase_{i}', {}).get('gates_executados', []):
                if 'alucinação' in gate.get('gate_id', '').lower() or 'alucinacao' in gate.get('descricao', '').lower():
                    if gate.get('status') == 'PASSOU':
                        fortes.append("✅ Zero alucinação — todas claims rastreadas")

        # 8. Código funcional implementado (phase 8)
        if tem_fase8 and dados['phase_8'].get('status') == 'COMPLETO':
            scripts = dados['phase_8'].get('processamento', {}).get('scripts_implementados', 0)
            testes = dados['phase_8'].get('processamento', {}).get('testes_passaram', 0)
            if scripts > 0:
                fortes.append(f"✅ Código funcional: {scripts} script(s) implementados, {testes} testes passando")

        if not fortes:
            fortes.append("✅ Projeto iniciado — dados coletados com sucesso")

        return fortes

    def _identificar_pontos_fracos(self, dados: Dict) -> List[str]:
        """Detectar pontos fracos a partir de dados reais"""
        fracos = []
        tem_fase8 = 'phase_8' in dados

        # 1. Phases faltando (fases 1-6 são obrigatórias; 7 é parte do pipeline padrão; 8 é opcional)
        phases_faltando = [
            i for i in range(1, 7)
            if dados.get(f'phase_{i}', {}).get('status') != 'COMPLETO'
        ]
        if phases_faltando:
            fracos.append(f"⚠️  Phases incompletas: {', '.join(str(p) for p in phases_faltando)}")

        # 2. Gates que falharam (inclui phase_8 se existir)
        for i in range(1, 9 if tem_fase8 else 7):
            for gate in dados.get(f'phase_{i}', {}).get('gates_executados', []):
                if gate.get('status') != 'PASSOU':
                    fracos.append(f"⚠️  Gate {gate.get('gate_id', '?')} falhou: {gate.get('descricao', '')}")

        # 3. Baixo determinismo (fases 1-7; phase 8 é 0% por natureza LLM)
        for i in range(1, 7):
            phase = dados.get(f'phase_{i}', {})
            det = phase.get('tokens', {}).get('percentual_determinismo', 0)
            if isinstance(det, str):
                det = int(det.replace('%', ''))
            if 0 < det < 50:
                fracos.append(f"⚠️  Phase {i} com determinismo baixo ({det}%)")

        # 5. Validações com falhas
        validacoes = dados.get('phase_1', {}).get('validacoes', {})
        if validacoes and validacoes.get('falhou', 0) > 0:
            fracos.append(f"⚠️  {validacoes['falhou']} validações falharam")

        # 6. Sem documentação
        if 'phase_6' not in dados or dados['phase_6'].get('status') != 'COMPLETO':
            fracos.append("⚠️  Sem documentação gerada (phase 6 incompleta)")

        # 7. Poucos gates definidos (base: fases 1-6; inclui 8 se existir)
        total_gates = sum(
            len(dados.get(f'phase_{i}', {}).get('gates_executados', []))
            for i in range(1, 9 if tem_fase8 else 7)
        )
        min_gates = 14 if tem_fase8 else 10
        if total_gates < min_gates:
            fracos.append(f"⚠️  Poucos gates definidos ({total_gates} — mínimo recomendado: {min_gates})")

        # 8. Intervenção manual necessária (inclui phase_8 se existir)
        for i in range(1, 9 if tem_fase8 else 7):
            resume = dados.get(f'phase_{i}', {}).get('resume_info', {})
            if resume.get('requer_intervencao_manual'):
                fracos.append(f"⚠️  Phase {i} requer intervenção manual")

        if not fracos:
            fracos.append("⚠️  Nenhum ponto fraco detectado — dados insuficientes para análise profunda")

        return fracos

    def _listar_requisitos_criticos(self, dados: Dict) -> List[Dict]:
        """Requisitos críticos derivados de gaps nos dados"""
        requisitos = []
        tem_fase8 = 'phase_8' in dados

        # 1. Phases incompletas → completar pipeline (fases 1-6 obrigatórias)
        phases_faltando = [
            i for i in range(1, 7)
            if dados.get(f'phase_{i}', {}).get('status') != 'COMPLETO'
        ]
        if phases_faltando:
            requisitos.append({
                'nome': f'Completar phases {", ".join(str(p) for p in phases_faltando)}',
                'horas': len(phases_faltando) * 15,
                'impacto': 'Completude',
            })

        # 2. Gates falhando → corrigir (inclui phase_8 se existir)
        gates_falha = []
        for i in range(1, 9 if tem_fase8 else 7):
            for gate in dados.get(f'phase_{i}', {}).get('gates_executados', []):
                if gate.get('status') != 'PASSOU':
                    gates_falha.append(gate.get('gate_id', '?'))
        if gates_falha:
            requisitos.append({
                'nome': f'Corrigir gates: {", ".join(gates_falha)}',
                'horas': len(gates_falha) * 8,
                'impacto': 'Qualidade',
            })

        # 3. Baixo determinismo → aumentar (fases 1-6; phase 8 é 0% por natureza)
        phases_baixo_det = []
        for i in range(1, 7):
            phase = dados.get(f'phase_{i}', {})
            det = phase.get('tokens', {}).get('percentual_determinismo', 0)
            if isinstance(det, str):
                det = int(det.replace('%', ''))
            if 0 < det < 60:
                phases_baixo_det.append(i)
        if phases_baixo_det:
            requisitos.append({
                'nome': f'Aumentar determinismo em phases {", ".join(str(p) for p in phases_baixo_det)}',
                'horas': len(phases_baixo_det) * 10,
                'impacto': 'Determinismo',
            })

        # 4. Sem documentação
        if 'phase_6' not in dados or dados['phase_6'].get('status') != 'COMPLETO':
            requisitos.append({
                'nome': 'Gerar documentação completa',
                'horas': 20,
                'impacto': 'Transparência',
            })

        # 5. Poucos gates → adicionar mais (base: fases 1-6; inclui 8 se existir)
        total_gates = sum(
            len(dados.get(f'phase_{i}', {}).get('gates_executados', []))
            for i in range(1, 9 if tem_fase8 else 7)
        )
        min_gates = 19 if tem_fase8 else 15
        if total_gates < min_gates:
            requisitos.append({
                'nome': f'Expandir cobertura de gates ({total_gates} → {min_gates}+)',
                'horas': 20,
                'impacto': 'Robustez',
            })

        # 6. Validações falhando
        validacoes = dados.get('phase_1', {}).get('validacoes', {})
        if validacoes and validacoes.get('falhou', 0) > 0:
            requisitos.append({
                'nome': 'Resolver validações com falha',
                'horas': 10,
                'impacto': 'Confiabilidade',
            })

        # 7. Economia fraca (fases 1-6; phase 8 tokens são LLM por natureza)
        for i in range(1, 7):
            phase = dados.get(f'phase_{i}', {})
            consumed = phase.get('tokens', {}).get('consumidos', 0)
            if consumed > 1000:
                requisitos.append({
                    'nome': f'Otimizar consumo de tokens na phase {i}',
                    'horas': 8,
                    'impacto': 'Eficiência',
                })

        if not requisitos:
            requisitos.append({
                'nome': 'Nenhum requisito crítico — projeto saudável',
                'horas': 0,
                'impacto': 'Nenhum',
            })

        return requisitos

    def _gerar_roadmap(self, score: Dict) -> Dict:
        """Gerar roadmap personalizado até 100/100.

        Filtra fases já atingidas pelo score atual — um projeto com score 80
        não precisa das fases v3.0 (target 75), apenas v4.0+.
        """
        todas_fases = [
            {
                'versao': 'v3.0',
                'target_score': 75,
                'titulo': 'Agência com Feedback Loops',
                'horas': 250,
                'timeline': '3 meses',
            },
            {
                'versao': 'v4.0',
                'target_score': 85,
                'titulo': 'Produção Escalável',
                'horas': 150,
                'timeline': '2 meses',
            },
            {
                'versao': 'v5.0',
                'target_score': 95,
                'titulo': 'Learning Loop',
                'horas': 140,
                'timeline': '2 meses',
            },
            {
                'versao': 'v6.0',
                'target_score': 100,
                'titulo': 'Maestro Agêntico',
                'horas': 50,
                'timeline': '1 mês',
            },
        ]

        score_atual = score['total']
        fases_restantes = [f for f in todas_fases if f['target_score'] > score_atual]

        return {
            'score_atual': score_atual,
            'fases': fases_restantes,
        }

    def _calcular_investimento(self, roadmap: Dict) -> Dict:
        """Calcular investimento necessário.

        ATENÇÃO: valores abaixo são ESTIMATIVAS baseadas em premissas fixas,
        não medições reais. Servem como ordem de magnitude para planejamento.

        Premissas:
        - Custo por hora: 150 USD (mercado BR pleno, ajustar conforme realidade)
        - Carga horária: 40h/semana × 4 semanas = 160h/mês por engenheiro
        """
        total_horas = sum(f['horas'] for f in roadmap['fases'])
        horas_por_engenheiro = 40 * 4  # 4 semanas por fase
        engenheiros_necessarios = max(1, total_horas // horas_por_engenheiro)
        custo_por_hora = 150  # USD — premissa, não medição

        return {
            'total_horas': total_horas,
            'engenheiros_necessarios': engenheiros_necessarios,
            'custo_total': (total_horas * custo_por_hora) // 1000,  # em k
            'timeline_meses': sum(int(f['timeline'].split()[0]) for f in roadmap['fases']),
            'premissas': {
                'custo_por_hora_usd': custo_por_hora,
                'horas_por_semana': 40,
                'nota': 'Estimativa — ajustar conforme mercado e equipe reais',
            },
        }

    def _consolidar_tokens_por_origem(self, dados: Dict) -> Dict:
        """Consolida tokens consumidos segregando por confiabilidade/origem de medição.
        Nunca soma tokens autodeclarados e medidos como se tivessem a mesma confiabilidade."""
        medido_api = 0
        autodeclarado = 0
        por_fase = {}

        for i in range(1, 9):
            chave = f'phase_{i}'
            if chave not in dados:
                continue
            phase = dados[chave]
            tokens_obj = phase.get('tokens', {})
            consumidos = tokens_obj.get('consumidos')
            origem = tokens_obj.get('origem_medicao')

            if not origem:
                if consumidos == 0 or consumidos is None:
                    origem = 'indisponivel' if consumidos is None else 'nao_aplicavel'
                else:
                    origem = 'autodeclarado'

            if isinstance(consumidos, (int, float)):
                c_val = int(consumidos)
                if origem == 'medido_api':
                    medido_api += c_val
                elif origem == 'autodeclarado':
                    autodeclarado += c_val
            else:
                c_val = None

            por_fase[chave] = {
                'consumidos': c_val,
                'origem_medicao': origem,
            }

        texto_consolidado = f"{medido_api} tokens medidos via API + {autodeclarado} tokens autodeclarados pela ADE"

        return {
            'total_medido_api': medido_api,
            'total_autodeclarado': autodeclarado,
            'total_consumidos': medido_api + autodeclarado,
            'consolidado_texto': texto_consolidado,
            'por_fase': por_fase,
        }

    def _md_secao_score(self, resultado: Dict) -> str:
        """Seção do relatório: cabeçalho + score atual por dimensão."""
        md = f"""# 📊 AUTO-CRÍTICA: Projeto {self.pasta_projeto.name}

**Gerado em:** {datetime.now().strftime('%d/%m/%Y %H:%M')}

## 🎯 Score Atual

**{resultado['score']['total']}/100** — {resultado['score']['classificacao']}

### Por Dimensão

| Dimensão | Score |
|----------|-------|"""
        for dim, score in resultado['score']['por_dimensao'].items():
            md += f"\n| {dim.replace('_', ' ').title()} | {score}/100 |"
        return md

    @staticmethod
    def _md_secao_pontos(resultado: Dict) -> str:
        """Seção do relatório: pontos fortes e pontos a melhorar."""
        md = """

## ✅ Pontos Fortes

"""
        for ponto in resultado['pontos_fortes']:
            md += f"- {ponto}\n"

        md += """

## ⚠️ Pontos a Melhorar

"""
        for ponto in resultado['pontos_fracos']:
            md += f"- {ponto}\n"
        return md

    @staticmethod
    def _md_secao_requisitos(resultado: Dict) -> str:
        """Seção do relatório: requisitos críticos dos próximos 12 meses."""
        md = """

## 🔴 Requisitos Críticos (Próximos 12 meses)

| Requisito | Horas | Impacto |
|-----------|-------|---------|"""
        for req in resultado['requisitos'][:5]:
            md += f"\n| {req['nome']} | {req['horas']}h | {req['impacto']} |"
        return md

    @staticmethod
    def _md_secao_roadmap(resultado: Dict) -> str:
        """Seção do relatório: roadmap para 100/100."""
        md = """

## 🚀 Roadmap para 100/100

"""
        for fase in resultado['roadmap']['fases']:
            md += f"""
### {fase['versao']}: {fase['titulo']}
- **Target:** {fase['target_score']}/100
- **Horas:** {fase['horas']}h
- **Timeline:** {fase['timeline']}
"""
        return md

    @staticmethod
    def _md_secao_investimento(resultado: Dict) -> str:
        """Seção do relatório: investimento necessário e consumo de tokens."""
        md = f"""

## 💰 Investimento Necessário

- **Total:** {resultado['investimento']['total_horas']}h
- **Equipe:** {resultado['investimento']['engenheiros_necessarios']} engenheiros
- **Custo:** ${resultado['investimento']['custo_total']}k
- **Timeline:** ~{resultado['investimento']['timeline_meses']} meses
- **Premissas:** {resultado['investimento']['premissas']['custo_por_hora_usd']} USD/hora, {resultado['investimento']['premissas']['horas_por_semana']}h/semana ({resultado['investimento']['premissas']['nota']})
"""
        tok_info = resultado.get('tokens_consolidado')
        if tok_info:
            md += f"""
## 🪙 Consumo de Tokens por Origem de Medição

- **Tokens Medidos via API (litellm):** {tok_info['total_medido_api']}
- **Tokens Autodeclarados pela ADE (não-verificáveis):** {tok_info['total_autodeclarado']}
- **Consolidação:** {tok_info['consolidado_texto']}
"""
        return md

    @staticmethod
    def _md_secao_recomendacao(resultado: Dict) -> str:
        """Seção do relatório: recomendação final e rodapé."""
        md = """
## 📌 Recomendação
"""
        total_h = resultado['investimento']['total_horas']
        fases_roadmap = resultado['roadmap']['fases']

        if total_h > 0 and fases_roadmap:
            primeira = fases_roadmap[0]
            md += f"""
Este projeto precisa de **{total_h}+ horas estimadas** para chegar a produção plena (estimativa, não medição).

**Sugestão:** Comece com {primeira['versao']} ({primeira['titulo']}) se quiser evoluir para produção.
"""
        else:
            md += """
Projeto com score máximo — foco em manutenção e evolução incremental.
"""

        md += """
---

**Lei Fundamental:** Nada oculto. Análise honesta. Sempre.
"""
        return md

    def _gerar_relatorio_markdown(self, resultado: Dict) -> str:
        """Gerar relatório markdown completo"""
        return (
            self._md_secao_score(resultado)
            + self._md_secao_pontos(resultado)
            + self._md_secao_requisitos(resultado)
            + self._md_secao_roadmap(resultado)
            + self._md_secao_investimento(resultado)
            + self._md_secao_recomendacao(resultado)
        )

    def _salvar_artefatos(self, artefatos: Dict):
        """Salvar análise e roadmap"""
        # Salvar AVALIACAO-AUTO-CRITICA.md na raiz do projeto
        path_relatorio = self.pasta_projeto / 'AVALIACAO-AUTO-CRITICA.md'
        with open(path_relatorio, 'w', encoding='utf-8') as f:
            f.write(artefatos['relatorio'])

        # Salvar ROADMAP-EVOLUCAO.md em .aidd/
        path_roadmap = self.pasta_projeto / '.aidd' / 'ROADMAP-EVOLUCAO.md'
        path_roadmap.parent.mkdir(parents=True, exist_ok=True)
        with open(path_roadmap, 'w', encoding='utf-8') as f:
            f.write("# 🚀 Roadmap de Evolução\n\n")
            f.write(artefatos['relatorio'])

        tok_info = artefatos.get('tokens_consolidado', {})

        # Salvar index JSON
        index = {
            'fase_id': 'phase_07_auto_critique',
            'versao': '2.1+',
            'status': 'COMPLETO',
            'timestamps': {
                'data_realizacao': datetime.now(timezone.utc).isoformat(),
            },
            'tokens': {
                'consumidos': 0,
                'economizados': 0,
                'percentual_determinismo': 100,
                'total_medido_api': tok_info.get('total_medido_api', 0),
                'total_autodeclarado': tok_info.get('total_autodeclarado', 0),
                'consolidado_texto': tok_info.get('consolidado_texto', ''),
                'por_fase': tok_info.get('por_fase', {}),
            },
            'processamento': {
                'score_calculado': artefatos['score']['total'],
                'pontos_fortes': len(artefatos['pontos_fortes']),
                'pontos_fracos': len(artefatos['pontos_fracos']),
                'requisitos_criticos': len(artefatos['roadmap']['fases']),
                'mapa_secoes_gerado': bool(artefatos.get('mapa_secoes')),
            },
            'resume_info': {
                'proxima_fase': 'Nenhuma (projeto gerado completo)',
                'pode_prosseguir': True,
                'projeto_pronto': True,
            }
        }

        path_index = self.cache_path / '_phase_07_index.json'
        with open(path_index, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2, ensure_ascii=False)


# =============================================================================
# ENTRY POINT
# =============================================================================

def main():
    """CLI para executar Phase 7"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Phase 7: Analisador Crítico Automático'
    )
    parser.add_argument('projeto',
                       help='Caminho do projeto a analisar')
    parser.add_argument('--cache-dir',
                       default=None,
                       help='Diretório de cache (default: projeto/.aidd/cache)')

    args = parser.parse_args()

    pasta_projeto = Path(args.projeto)

    if not pasta_projeto.exists():
        print(f"❌ Projeto não encontrado: {pasta_projeto}")
        sys.exit(1)

    analisador = AnalisadorCriticoAutomatico(pasta_projeto)
    resultado = analisador.executar()

    if resultado['status'] != 'COMPLETO':
        sys.exit(1)

    sys.exit(0)


if __name__ == '__main__':
    main()
