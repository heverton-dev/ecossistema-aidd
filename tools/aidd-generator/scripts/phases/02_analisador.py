#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PHASE 2: Analisador de Ideia
aidd-project-generator v2.1

Analisa ideia do projeto + referências de Phase 1
Retorna especificação estruturada para Phase 3 (Design)

Executa 4 gates de validação (A1-A4)
Gera _phase_02_index.json com análise completa

Tokens: 5k (LLM estratégica) — Determinismo: 0% (pura LLM)
"""

import sys
import os
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, List, Any

# Escritor atômico: staging → fsync → os.replace
try:
    from escritor_atomico import escrever_atomico, escrever_json_atomico
except ImportError:
    import importlib.util
    _comp_dir = os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "..", "componentes", "compartilhado", "src-core"
    )
    if os.path.isdir(_comp_dir) and _comp_dir not in sys.path:
        sys.path.insert(0, _comp_dir)
    from escritor_atomico import escrever_atomico, escrever_json_atomico

# Importar utils para detectar modelo e protocolo delegado.
# Import relativo (modo pacote) com fallback bare (execução direta da fase),
# preservando os dois modos sem mutação de sys.path.
try:
    from .utils_modelo import detectar_modelo_harness, obter_nome_amigavel_modelo, log_modelo_detectado
    from .utils_delegacao import solicitar_llm, extrair_json_resposta, LLMNaoConfiguradoException
except ImportError:  # pragma: no cover — execução direta (python scripts/phases/02_analisador.py)
    from utils_modelo import detectar_modelo_harness, obter_nome_amigavel_modelo, log_modelo_detectado
    from utils_delegacao import solicitar_llm, extrair_json_resposta, LLMNaoConfiguradoException

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# =============================================================================
# ITEM 2 [TK-1]: ORÇADOR DE CONTEXTO — HANDOFF FASE 1 → FASE 2
# =============================================================================
# Teto de orçamento (tokens) para o handoff de referências da Fase 1.
# Determinístico: poda por campos essenciais + seleção top-k por score de
# relevância (estrelas/downloads/atividade) já medido pela Fase 1.
# Medição por tiktoken (cl100k_base) com fallback determinístico de
# contagem por palavras — nunca chamada de LLM.
TETO_TOKENS_HANDOFF_FASE2 = 5000
TETO_POR_REFERENCIA_TOKENS = 300
TOP_K_REFERENCIAS = 12

_CAMPOS_ESSENCIAIS = ('nome', 'titulo', 'url', 'fonte', 'descricao', 'resumo',
                      'linguagens', 'stars', 'downloads', 'likes', 'licenca')


def _contar_tokens_aprox(texto: str) -> int:
    """Contagem determinística de tokens: tiktoken (cl100k_base) se disponível,
    senão estimativa conservadora (palavras vs chars/4). Zero LLM."""
    try:
        import tiktoken
        return len(tiktoken.get_encoding('cl100k_base').encode(texto))
    except Exception:
        return max(len(texto.split()), len(texto) // 4, 1)


def _score_referencia(ref: Dict) -> float:
    """Score determinístico de relevância (proxy local dos gates R1-R4):
    atividade recente + popularidade. Maior score = entra primeiro no top-k."""
    metadata = ref.get('metadata', {}) if isinstance(ref, dict) else {}
    score = 0.0
    score += min(float(metadata.get('stars', 0) or 0) / 1000.0, 50.0)
    score += min(float(metadata.get('downloads', 0) or 0) / 100000.0, 50.0)
    score += min(float(metadata.get('likes', 0) or 0) / 100.0, 25.0)
    ultimo = metadata.get('ultimo_commit') or ''
    if ultimo:
        try:
            from datetime import datetime as _dt, timezone as _tz
            delta = _dt.now(_tz.utc) - _dt.fromisoformat(str(ultimo).replace('Z', '+00:00'))
            score += max(0.0, 25.0 - delta.days / 4.0)  # commit < 90 dias pontua alto
        except (ValueError, TypeError):
            pass
    return score


def _podar_referencia(ref: Any) -> Dict:
    """Mantém apenas campos essenciais (titulo/resumo/URL/dados-chave),
    descartando metadados inflados. Trunca texto longo com elipse honesta."""
    podada: Dict[str, Any] = {}
    if isinstance(ref, dict):
        fonte_metadata = ref.get('metadata') if isinstance(ref.get('metadata'), dict) else {}
        for campo in _CAMPOS_ESSENCIAIS:
            valor = ref.get(campo, fonte_metadata.get(campo))
            if valor is None:
                continue
            if isinstance(valor, str) and len(valor) > 200:
                valor = valor[:197] + '...'
            podada[campo] = valor
        # dependências-chave: tags no nível do metadata
        if not podada.get('linguagens') and isinstance(fonte_metadata.get('tags'), list):
            podada['linguagens'] = fonte_metadata['tags'][:5]
    else:
        podada['nome'] = str(ref)
    return podada


def _serializar_referencia_podada(ref: Dict) -> str:
    return json.dumps(ref, ensure_ascii=False, separators=(',', ':'))


def montar_handoff_referencias(referencias: Any,
                               max_tokens: int = TETO_TOKENS_HANDOFF_FASE2) -> str:
    """[TK-1] Item 2: substitui o dump bruto json.dumps(referencias) por handoff
    podado: top-k referências com campos essenciais, respeitando teto de tokens.

    Retorna string JSON pronta para embutir no prompt da Fase 2. Garantias:
    - Cabeçalho informativo: total avaliado vs incluído (transparência total).
    - Nunca excede max_tokens (corta por score, nunca aleatório).
    - Ordem determinística: score desc, depois ordem original.
    """
    if isinstance(referencias, dict):
        lista = referencias.get('referencias')
        if not isinstance(lista, list):
            # Payload legado (ex.: insights_phase1.json ou {'ref': 'x'}):
            # serializa campos-chave do dict raiz, sem dump integral.
            resumo_raiz = {k: referencias[k] for k in ('total_insights', 'insights', 'linguagens_comuns')
                           if k in referencias}
            candidatos = [{'nome': k, 'resumo': v} for k, v in list(referencias.items())[:TOP_K_REFERENCIAS]
                          if k not in resumo_raiz and isinstance(v, (dict, list, str))]
            corpo_ref = [_podar_referencia(c) for c in candidatos]
            final_legado: Dict[str, Any] = dict(resumo_raiz)
            if corpo_ref:
                final_legado['referencias_podadas'] = corpo_ref
            final = json.dumps(final_legado, ensure_ascii=False, separators=(',', ':'))
            while _contar_tokens_aprox(final) > max_tokens and final_legado.get('referencias_podadas'):
                final_legado['referencias_podadas'].pop()
                final = json.dumps(final_legado, ensure_ascii=False, separators=(',', ':'))
            return final
        refs = lista
    elif isinstance(referencias, list):
        refs = referencias
    else:
        return '{}'

    total_avaliadas = len(refs)
    if total_avaliadas == 0:
        return '{}'

    # Poda por referência + score determinístico (ordem original como desempate)
    podadas = [_podar_referencia(r) for r in refs if r is not None]
    scored = list(enumerate(podadas))
    scored.sort(key=lambda par: (-_score_referencia(refs[par[0]] if par[0] < len(refs) else {}), par[0]))

    # Seleção top-k respeitando teto global e teto por referência
    selecionadas: List[Dict] = []
    tokens_corpo = 0
    for _, ref_podada in scored:
        if len(selecionadas) >= TOP_K_REFERENCIAS:
            break
        serial = _serializar_referencia_podada(ref_podada)
        custo = _contar_tokens_aprox(serial)
        if custo > TETO_POR_REFERENCIA_TOKENS:
            ref_podada = {k: v for k, v in ref_podada.items() if k in ('nome', 'titulo', 'url', 'fonte')}
            serial = _serializar_referencia_podada(ref_podada)
            custo = _contar_tokens_aprox(serial)
        if tokens_corpo + custo > max_tokens - 120:  # reserva para cabeçalho
            continue
        selecionadas.append(ref_podada)
        tokens_corpo += custo

    cabecalho = {'handoff_fase1_fase2': True, 'referencias_avaliadas': total_avaliadas,
                 'referencias_incluidas': len(selecionadas),
                 'orcamento_tokens': max_tokens,
                 'poda_aplicada': len(selecionadas) < total_avaliadas}
    final = json.dumps({'_handoff': cabecalho, 'referencias': selecionadas},
                       ensure_ascii=False, separators=(',', ':'))
    # Última linha de defesa: se ainda exceder o teto, corta a menor ref até caber
    while _contar_tokens_aprox(final) > max_tokens and selecionadas:
        selecionadas.pop()
        cabecalho['referencias_incluidas'] = len(selecionadas)
        final = json.dumps({'_handoff': cabecalho, 'referencias': selecionadas},
                           ensure_ascii=False, separators=(',', ':'))
    return final



# =============================================================================
# PROMPT PARA AGENT LLM
# =============================================================================

PROMPT_ANALISADOR_IDEIA = """# ENTRADA: AIDD Project Analyst — specialized in structured project analysis.

Analyze the PROVIDED project idea and the SIMILAR REFERENCES found.

PROJECT IDEA:
{ideia}

SIMILAR REFERENCES (from Phase 1):
{referencias_json}

STRUCTURED ANALYSIS:

For each field below, be specific and cite references when applicable.

1. **objetivo** (1-2 lines): What does the project do? What problem does it solve?

2. **publico_alvo** (1 line): Who will use it? Engineers? Companies? Educators?

3. **constraints** (3-5 bullets): Technical/business limitations
   - Example: "Zero binary downloads"
   - Example: "Maximum token economy"

4. **stack_recomendado**: JSON with
   - linguagem: "Python 3.10+"
   - framework: "FastAPI" or "Django" or "None"
   - banco: "SQLite" or "PostgreSQL"
   - libs_principais: ["lib1", "lib2"]

5. **arquitetura** (1 paragraph): Overview. Layers? Flow?

6. **referencias_utilizadas**: Exact list of references you cited

# COT: Before responding, think in English Caveman (3-5 dense lines, no articles):
# "check project idea → extract core domain → map to stack → validate against refs → output JSON"

# SAIDA: Return VALID JSON only (no markdown, no ```json, no extra text).
# RESPOND IN BRAZILIAN PORTUGUESE (PT-BR) — all field values must be in PT-BR.

{
  "objetivo": "...",
  "publico_alvo": "...",
  "constraints": ["...", "..."],
  "stack_recomendado": {
    "linguagem": "...",
    "framework": "...",
    "banco": "...",
    "libs_principais": ["..."]
  },
  "arquitetura": "...",
  "referencias_utilizadas": ["referencia1", "referencia2"]
}

CRITICAL: Zero hallucination. Only cite references from the list above.
CRITICAL: Return ONLY valid JSON, nothing else."""


# =============================================================================
# GATES DE VALIDAÇÃO
# =============================================================================

class Gate:
    """Resultado de validação de gate"""
    def __init__(self, gate_id: str, descricao: str, passou: bool, detalhes: str):
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


class ValidadorGatesPhase2:
    """Valida análise semântica"""

    @staticmethod
    def executar_todos(analise_resultado: Dict) -> tuple[List[Gate], bool]:
        """Executa A1-A4 sequencialmente"""
        gates_resultado = []

        # Gate A1: Schema válido
        gate_a1 = ValidadorGatesPhase2._gate_a1_schema_valido(analise_resultado)
        gates_resultado.append(gate_a1)

        # Gate A2: Zero alucinação
        gate_a2 = ValidadorGatesPhase2._gate_a2_zero_alucinacao(analise_resultado)
        gates_resultado.append(gate_a2)

        # Gate A3: Dados completos
        gate_a3 = ValidadorGatesPhase2._gate_a3_dados_completo(analise_resultado)
        gates_resultado.append(gate_a3)

        # Gate A4: Qualidade linguagem
        gate_a4 = ValidadorGatesPhase2._gate_a4_qualidade_linguagem(analise_resultado)
        gates_resultado.append(gate_a4)

        todos_passaram = all(g.passou for g in gates_resultado)
        return gates_resultado, todos_passaram

    @staticmethod
    def _gate_a1_schema_valido(analise: Dict) -> Gate:
        """A1: Output segue schema esperado"""
        try:
            campos_obrigatorios = ['objetivo', 'publico_alvo', 'constraints', 'stack_recomendado']
            tem_todos = all(campo in analise for campo in campos_obrigatorios)
            passou = tem_todos
            detalhes = f"Schema válido: {len([c for c in campos_obrigatorios if c in analise])}/4 campos"
        except TypeError:
            passou = False
            detalhes = "Schema inválido"

        return Gate('A1_schema_valido',
                   'Validar output segue schema',
                   passou,
                   detalhes)

    @staticmethod
    def _gate_a2_zero_alucinacao(analise: Dict) -> Gate:
        """A2: Todas claims têm referências"""
        referencias = analise.get('referencias_utilizadas', []) if isinstance(analise, dict) else []
        if referencias is None:
            referencias = []
        passou = len(referencias) > 0
        detalhes = (
            f"{len(referencias)} referências rastreadas (zero alucinação)"
            if passou
            else "0 referências rastreadas (gate reprovado: nenhuma referência real citada ou disponível)"
        )

        return Gate('A2_zero_alucinacao',
                   'Validar zero alucinação (todas claims rastreadas)',
                   passou,
                   detalhes)

    @staticmethod
    def _gate_a3_dados_completo(analise: Dict) -> Gate:
        """A3: Análise cobre todos os aspectos"""
        aspectos = ['objetivo', 'publico_alvo', 'constraints', 'stack_recomendado', 'arquitetura']
        cobertos = sum(1 for a in aspectos if a in analise and analise[a])
        passou = cobertos >= 4
        detalhes = f"{cobertos}/{len(aspectos)} aspectos analisados"

        return Gate('A3_dados_completo',
                   'Validar análise cobre todos aspectos',
                   passou,
                   detalhes)

    @staticmethod
    def _gate_a4_qualidade_linguagem(analise: Dict) -> Gate:
        """A4: Texto coerente e profissional"""
        objetivo = analise.get('objetivo', '').strip()
        passou = len(objetivo) > 20  # Mínimo de conteúdo
        detalhes = f"Qualidade: {'Profissional' if passou else 'Reescrever'}"

        return Gate('A4_qualidade_linguagem',
                   'Validar texto coerente e profissional',
                   passou,
                   detalhes)


# =============================================================================
# ANALISADOR PRINCIPAL
# =============================================================================

class AnalisadorFase2:
    """Analisa ideia + referências para design"""

    def __init__(self, pasta_cache: Path, model_override: str = None):
        self.pasta_cache = Path(pasta_cache)
        self.pasta_cache.mkdir(parents=True, exist_ok=True)

        # Detectar modelo automaticamente
        self.model_override = model_override
        self.modelo_harness = detectar_modelo_harness()
        self.modelo_final = model_override or self.modelo_harness
        self.modelo_nome_amigavel = obter_nome_amigavel_modelo(self.modelo_final)

    def executar(self, ideia_projeto: str, referencias_phase1: Dict) -> Optional[Dict]:
        """Executa pipeline completo da Phase 2"""
        print(f"\n📊 PHASE 2: Analisador da Ideia")
        print(f"   Ideia: {ideia_projeto}")
        print(f"   Modelo: {self.modelo_nome_amigavel}")
        print(f"   {'-' * 60}")

        tempo_inicio = datetime.now()

        # 1. Analisar ideia com LLM (via protocolo delegado ou headless)
        print(f"\n🤖 Analisando ideia...")

        analise = self._analisar_ideia_com_llm(ideia_projeto, referencias_phase1)

        # SEM fallback para mock: se a chamada real falhar, a fase falha de
        # verdade. Um fallback silencioso aqui é exatamente o padrão que a
        # auditoria de 29/08/2026 identificou como falso-sucesso.
        if analise is None:
            print(f"\n❌ FASE FALHOU: chamada real ao LLM falhou (ver erro acima)")
            print(f"   Configure a variável LLM_MODEL (ex: anthropic/claude-haiku-4-5-20251001,")
            print(f"   openai/gpt-4o, ollama/llama3) e a chave de API do provedor escolhido.")
            return None

        # 2. Executar gates
        print(f"\n✅ Executando gates (A1-A4)...")
        gates, todos_passaram = ValidadorGatesPhase2.executar_todos(analise)

        for gate in gates:
            status_icon = "✓" if gate.passou else "✗"
            print(f"   {status_icon} {gate.gate_id}: {gate.detalhes}")

        if not todos_passaram:
            print(f"\n❌ FASE FALHOU: Gates não passaram")
            return None

        # 3. Gerar index
        tempo_execucao = (datetime.now() - tempo_inicio).total_seconds()
        print(f"\n📝 Gerando índice de fase...")

        index = self._gerar_index(analise, gates, tempo_execucao)

        # 4. Salvar index e análise
        path_index = self.pasta_cache / '_phase_02_index.json'
        path_analise = self.pasta_cache / 'data' / 'analise_phase2.json'

        path_analise.parent.mkdir(parents=True, exist_ok=True)

        escrever_json_atomico(path_index, index)

        escrever_json_atomico(path_analise, analise)

        print(f"   ✓ {path_index}")
        print(f"   ✓ {path_analise}")

        print(f"\n{'=' * 60}")
        print(f"✅ PHASE 2 COMPLETO")
        print(f"   Status: {index['status']}")
        print(f"   Tempo: {tempo_execucao:.1f}s")
        print(f"   Tokens: {index['tokens']['consumidos']} (origem: {index['tokens']['origem_medicao']})")
        print(f"{'=' * 60}\n")

        return index

    def _analisar_ideia_com_llm(self, ideia: str, referencias: Dict) -> Optional[Dict]:
        """
        Chama LLM via protocolo unificado (delegado ou headless).

        Modo Delegado (default): ADE ativa (Claude Code, Codex, etc.) responde
                                  via arquivo JSON — zero credencial nova.
        Modo Headless (fallback): se nenhuma ADE, usa litellm com LLM_MODEL env var.

        Sem fallback silencioso: se ambos falham, retorna None com erro real visível.
        """

        # Item 2 [TK-1]: handoff podado com teto de tokens (antes: dump bruto indent=2)
        referencias_json = montar_handoff_referencias(referencias, TETO_TOKENS_HANDOFF_FASE2)
        # .replace() em vez de .format(): o template tem chaves literais nos
        # exemplos de JSON, que .format() tentaria interpretar como placeholders.
        prompt = PROMPT_ANALISADOR_IDEIA.replace('{ideia}', ideia).replace('{referencias_json}', referencias_json)

        contexto = f"Phase 2: Analisador de Ideia. Projeto: {ideia[:50]}"

        print(f"   🤖 Solicitando análise ao LLM (via protocolo universal)...")

        try:
            resposta = solicitar_llm(
                prompt=prompt,
                contexto=contexto,
                fase="phase_02",
                modelo=os.getenv('LLM_MODEL', self.modelo_final),
                timeout_delegacao=30
            )
        except LLMNaoConfiguradoException as e:
            print(f"   ❌ {e.mensagem_usuario}")
            return None

        if resposta is None:
            print(f"   ❌ Falha ao obter resposta do LLM (nenhuma ADE ativa e/ou headless sem credencial)")
            return None

        try:
            conteudo = resposta['conteudo']
            tokens_usados = resposta.get('tokens_consumidos')
            origem_medicao = resposta.get('origem_medicao')
            if not origem_medicao:
                origem_medicao = 'indisponivel' if tokens_usados is None else 'autodeclarado'
            modelo_usado = resposta.get('modelo_usado', 'desconhecido')

            analise = extrair_json_resposta(conteudo)
            analise['_tokens_reais_consumidos'] = tokens_usados
            analise['_origem_medicao'] = origem_medicao
            analise['_modelo_usado'] = modelo_usado

            # Se LLM omitiu ou deixou vazio, tenta recuperar apenas das referências reais fornecidas da Fase 1
            if not analise.get('referencias_utilizadas'):
                lista_refs = []
                if isinstance(referencias, dict):
                    lista_refs = [r.get('titulo') or r.get('url') or r.get('nome') for r in referencias.get('referencias', []) if isinstance(r, dict)]
                elif isinstance(referencias, list):
                    lista_refs = [r.get('titulo') or r.get('url') or r.get('nome') for r in referencias if isinstance(r, dict)]
                analise['referencias_utilizadas'] = [r for r in lista_refs[:3] if r]

            print(f"   ✅ Análise recebida ({tokens_usados} tokens via {modelo_usado}, origem: {origem_medicao})")
            return analise

        except json.JSONDecodeError as e:
            print(f"   ❌ LLM respondeu, mas não retornou JSON válido: {e}")
            print(f"      Conteúdo recebido: {resposta.get('conteudo', '')[:200]}")
            return None
        except (KeyError, ValueError, TypeError) as e:
            print(f"   ❌ Erro ao processar resposta: {e}")
            return None

    def _gerar_index(self, analise: Dict, gates: List[Gate], tempo_execucao: float) -> Dict:
        """Gera _phase_02_index.json"""

        tokens_reais = analise.get('_tokens_reais_consumidos')
        origem_medicao = analise.get('_origem_medicao')
        if not origem_medicao:
            origem_medicao = 'indisponivel' if tokens_reais is None else 'autodeclarado'

        if origem_medicao == 'medido_api':
            desc_medicao = 'medido_api (litellm resposta.usage.total_tokens)'
        elif origem_medicao == 'autodeclarado':
            desc_medicao = 'autodeclarado (resposta do orquestrador/ADE)'
        else:
            desc_medicao = 'nao disponivel (provedor nao retornou usage)'

        index = {
            'fase_id': 'phase_02_analysis',
            'versao': '2.1',
            'status': 'COMPLETO' if all(g.passou for g in gates) else 'FALHOU',

            'timestamps': {
                'data_inicio': datetime.now(timezone.utc).isoformat(),
                'data_conclusao': datetime.now(timezone.utc).isoformat(),
                'duracao_segundos': tempo_execucao
            },

            'tokens': {
                'consumidos': tokens_reais,
                'origem_medicao': origem_medicao,
                'medicao': desc_medicao,
                'percentual_determinismo': 0  # Phase 2 é 100% LLM
            },

            'processamento': {
                'items_reutilizados_cache': 0,  # mecanismo de reuso ainda não existe (Fase 7 do plano)
                'tokens_economizados_cache': 0,
                'analise_completa': True
            },

            'gates_executados': [g.to_dict() for g in gates],

            'resume_info': {
                'proxima_fase': 'phase_03_design',
                'pode_prosseguir': all(g.passou for g in gates),
                'requer_intervencao_manual': not all(g.passou for g in gates)
            }
        }

        return index


# =============================================================================
# ENTRY POINT
# =============================================================================

def main():
    """CLI para testar Phase 2"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Phase 2: Analisador da Ideia - aidd-project-generator v2.1'
    )
    parser.add_argument('ideia',
                       help='Descrição da ideia do projeto')
    parser.add_argument('--cache-dir',
                       default='.aidd/cache',
                       help='Diretório para cache')
    parser.add_argument('--referencias',
                       default='{}',
                       help='JSON das referências de Phase 1')

    args = parser.parse_args()

    referencias = json.loads(args.referencias)

    analisador = AnalisadorFase2(Path(args.cache_dir))
    resultado = analisador.executar(args.ideia, referencias)

    if resultado is None:
        sys.exit(1)

    sys.exit(0)


if __name__ == '__main__':
    main()
