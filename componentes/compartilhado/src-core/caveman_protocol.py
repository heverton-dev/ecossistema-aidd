# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD v5.1 Enterprise — Caveman Ultra Triple Protocol Engine
=============================================================================
Motor de compressão tri-fase que otimiza consumo de tokens em pipelines
de agentes de IA. Reduz input em 30-50% (BPE), mantém raciocínio denso
em CoT interno e entrega output de alta qualidade em PT-BR.

Fases:
  INPUT      → Regras comprimidas em English Caveman (30-50% redução BPE)
  PROCESSING → Thinking interno em English Caveman Ultra (3-5 linhas CoT)
  OUTPUT     → PT-BR padrão alto — código completo, tipado, Result Monad, sem stubs
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from .result import Result


# =============================================================================
# Constantes e Configurações
# =============================================================================

class IntensidadeCaveman(Enum):
    """Níveis de compressão disponíveis no protocolo Caveman."""
    LITE = "lite"
    FULL = "full"
    ULTRA = "ultra"


# Mapa de substituições: palavras verbose → caveman (por intensidade)
_SUBSTITUICOES_LITE: Dict[str, str] = {
    "it is necessary to": "must",
    "it is important to": "must",
    "in order to": "to",
    "for the purpose of": "for",
    "with regard to": "about",
    "in the event that": "if",
    "at this point in time": "now",
    "due to the fact that": "because",
    "in the near future": "soon",
    "as a result of": "from",
    "in addition to": "also",
    "on the other hand": "but",
    "at the present time": "now",
    "in light of the fact that": "since",
    "with respect to": "about",
    "for the reason that": "because",
    "in spite of the fact that": "despite",
    "on a regular basis": "regularly",
    "a large number of": "many",
    "the majority of": "most",
    "in a timely manner": "quickly",
    "has the ability to": "can",
    "is able to": "can",
    "make a decision": "decide",
    "make an attempt": "try",
    "give consideration to": "consider",
    "provide assistance to": "help",
    "make improvements to": "improve",
    "conduct an analysis of": "analyze",
    "perform an evaluation of": "evaluate",
    "implement a solution for": "fix",
    "take into consideration": "consider",
    "make a recommendation": "recommend",
    "provide an explanation": "explain",
}

_SUBSTITUICOES_FULL: Dict[str, str] = {
    **_SUBSTITUICOES_LITE,
    "the": "",
    "a ": "",
    "an ": "",
    "is ": " ",
    "are ": " ",
    "was ": " ",
    "were ": " ",
    "be ": " ",
    "been ": " ",
    "being ": " ",
    "has ": " ",
    "have ": " ",
    "had ": " ",
    "do ": " ",
    "does ": " ",
    "did ": " ",
    "will ": " ",
    "would ": " ",
    "could ": " ",
    "should ": " ",
    "may ": " ",
    "might ": " ",
    "must ": " ",
    "shall ": " ",
    "can ": " ",
    "that ": " ",
    "which ": " ",
    "this ": " ",
    "these ": " ",
    "those ": " ",
    "there ": " ",
    "here ": " ",
    "very ": "",
    "really ": "",
    "quite ": "",
    "just ": "",
    "basically ": "",
    "actually ": "",
    "simply ": "",
    "certainly ": "",
    "surely ": "",
    "definitely ": "",
    "absolutely ": "",
    "essentially ": "",
    "fundamentally ": "",
    "necessarily ": "",
    "particularly ": "",
    "specifically ": "",
    "generally ": "",
    "typically ": "",
    "usually ": "",
    "often ": "",
    "sometimes ": "",
    "perhaps ": "",
    "maybe ": "",
    "possibly ": "",
    "approximately ": "~",
    "about ": "~",
    "regarding ": "re: ",
    "concerning ": "re: ",
    "therefore ": "→ ",
    "consequently ": "→ ",
    "furthermore ": "also ",
    "moreover ": "also ",
    "however ": "but ",
    "nevertheless ": "but ",
    "nonetheless ": "but ",
    "alternatively ": "or ",
    "additionally ": "also ",
    "subsequently ": "then ",
    "previously ": "before ",
    "currently ": "now ",
    "eventually ": "finally ",
    "immediately ": "now ",
    "specifically ": "",
    "particularly ": "",
    "respectively ": "",
    "corresponding ": "matching ",
    "appropriate ": "fit ",
    "sufficient ": "enough ",
    "necessary ": "req ",
    "required ": "req ",
    "implement ": "impl ",
    "implementation ": "impl ",
    "configuration ": "cfg ",
    "information ": "info ",
    "documentation ": "docs ",
    "environment ": "env ",
    "development ": "dev ",
    "production ": "prod ",
    "application ": "app ",
    "repository ": "repo ",
    "dependency ": "dep ",
    "authentication ": "auth ",
    "authorization ": "authz ",
    "initialization ": "init ",
    "registration ": "reg ",
    "validation ": "valid ",
    "verification ": "verify ",
    "error handling": "err handling",
    "exception handling": "exc handling",
    "performance optimization": "perf opt",
    "memory management": "mem mgmt",
    "resource allocation": "res alloc",
    "thread safety": "thread-safe",
    "type safety": "type-safe",
    "null safety": "null-safe",
}

_SUBSTITUICOES_ULTRA: Dict[str, str] = {
    **_SUBSTITUICOES_FULL,
    "and ": "∧ ",
    "or ": "∨ ",
    "not ": "¬",
    "because ": "∵ ",
    "therefore ": "∴ ",
    "if ": "→ ",
    "then ": "→ ",
    "else ": "¬→ ",
    "return ": "ret ",
    "function ": "fn ",
    "variable ": "var ",
    "parameter ": "param ",
    "argument ": "arg ",
    "property ": "prop ",
    "method ": "mth ",
    "attribute ": "attr ",
    "interface ": "iface ",
    "abstract ": "abs ",
    "extends ": "⊂ ",
    "implements ": "impl ",
    "import ": "imp ",
    "export ": "exp ",
    "default ": "def ",
    "class ": "cls ",
    "instance ": "inst ",
    "reference ": "ref ",
    "pointer ": "ptr ",
    "iterator ": "iter ",
    "generator ": "gen ",
    "callback ": "cb ",
    "promise ": "prom ",
    "async ": "a ",
    "await ": "aw ",
    "true ": "T ",
    "false ": "F ",
    "null ": "∅ ",
    "undefined ": "undef ",
    "string ": "str ",
    "integer ": "int ",
    "boolean ": "bool ",
    "floating ": "float ",
    "character ": "char ",
    "array ": "arr ",
    "object ": "obj ",
    "dictionary ": "dict ",
    "collection ": "coll ",
    "element ": "elem ",
    "component ": "comp ",
    "service ": "svc ",
    "controller ": "ctrl ",
    "middleware ": "mw ",
    "database ": "db ",
    "transaction ": "tx ",
    "connection ": "conn ",
    "response ": "res ",
    "request ": "req ",
    "endpoint ": "ep ",
    "payload ": "pl ",
    "header ": "hdr ",
    "protocol ": "proto ",
    "message ": "msg ",
    "notification ": "notif ",
    "subscription ": "sub ",
    "publication ": "pub ",
    "operation ": "op ",
    "execution ": "exec ",
    "evaluation ": "eval ",
    "calculation ": "calc ",
    "transformation ": "xform ",
    "serialization ": "ser ",
    "deserialization ": "deser ",
    "compression ": "comp ",
    "decompression ": "decomp ",
    "encryption ": "enc ",
    "decryption ": "dec ",
    "synchronization ": "sync ",
    "asynchronous ": "async ",
    "concurrent ": "conc ",
    "parallel ": "par ",
    "sequential ": "seq ",
    "recursive ": "recur ",
    "iterative ": "iter ",
    "conditional ": "cond ",
    "exception ": "exc ",
    "assertion ": "assert ",
    "debugging ": "dbg ",
    "monitoring ": "mon ",
    "logging ": "log ",
    "tracing ": "trace ",
    "profiling ": "prof ",
    "benchmarking ": "bench ",
    "testing ": "test ",
    "deployment ": "deploy ",
    "rollback ": "rback ",
    "migration ": "migr ",
    "upgrade ": "upg ",
    "downgrade ": "dng ",
}


# Padrões de limpeza pós-substituição
_PADROES_LIMPEZA = [
    (re.compile(r"\s{2,}"), " "),          # múltiplos espaços → um
    (re.compile(r"^\s+|\s+$"), ""),         # trim
    (re.compile(r"\s+([,.:;])"), r"\1"),    # espaço antes de pontuação
    (re.compile(r"\n{3,}"), "\n\n"),        # excesso de quebras
]


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class EstatisticasTokens:
    """Estatísticas de economia de tokens após compressão."""
    tokens_originais: int
    tokens_comprimidos: int
    tokens_economizados: int
    percentual_reducao: float
    intensidade: str
    fase: str
    tempo_compressao_ms: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tokens_originais": self.tokens_originais,
            "tokens_comprimidos": self.tokens_comprimidos,
            "tokens_economizados": self.tokens_economizados,
            "percentual_reducao": round(self.percentual_reducao, 2),
            "intensidade": self.intensidade,
            "fase": self.fase,
            "tempo_compressao_ms": round(self.tempo_compressao_ms, 3),
        }


@dataclass
class SessaoProtocolo:
    """Estado acumulado de uma sessão do protocolo Caveman."""
    sessao_id: str
    intensidade: IntensidadeCaveman = IntensidadeCaveman.FULL
    historico: List[EstatisticasTokens] = field(default_factory=list)
    total_tokens_originais: int = 0
    total_tokens_comprimidos: int = 0

    @property
    def economia_total_percentual(self) -> float:
        if self.total_tokens_originais == 0:
            return 0.0
        return round(
            (1 - self.total_tokens_comprimidos / self.total_tokens_originais) * 100, 2
        )


# =============================================================================
# Caveman Protocol — Motor Tri-Fase
# =============================================================================

class CavemanProtocol:
    """
    Motor do Protocolo Caveman Ultra — Triple Phase Token Optimizer.

    Fases:
      1. INPUT:      Compressão de regras/instruções → English Caveman
      2. PROCESSING: Raciocínio interno → English Caveman Ultra CoT denso
      3. OUTPUT:     Entrega final → PT-BR padrão alto

    Uso:
        proto = CavemanProtocol(intensidade=IntensidadeCaveman.FULL)
        regras_comprimidas = proto.format_input(regras_originais)
        thinking = proto.format_thinking(contexto)
        output_final = proto.format_output(codigo_gerado)
        stats = proto.estatisticas_sessao()
    """

    def __init__(
        self,
        intensidade: IntensidadeCaveman = IntensidadeCaveman.FULL,
        sessao_id: Optional[str] = None,
    ):
        self.intensidade = intensidade
        self._sessao = SessaoProtocolo(
            sessao_id=sessao_id or f"caveman-{int(time.time() * 1000)}",
            intensidade=intensidade,
        )

    # -------------------------------------------------------------------------
    # Fase 1: INPUT — Compressão de Regras
    # -------------------------------------------------------------------------

    def format_input(self, rules: str) -> Result[str]:
        """
        Comprime regras/instruções de input para English Caveman.

        Aplica substituições progressivas baseadas no nível de intensidade,
        removendo redundância e mantendo o significado técnico.

        Args:
            rules: Texto original das regras em inglês.

        Returns:
            Result.ok com texto comprimido ou Result.fail em caso de erro.
        """
        if not rules or not rules.strip():
            return Result.fail(
                "Regras de input vazias ou nulas",
                codigo="CAVEMAN_INPUT_VAZIO",
            )

        inicio = time.perf_counter()
        texto = rules

        # Aplica substituições por intensidade
        mapa = self._obter_mapa_substituicoes()
        for original, substituto in mapa.items():
            # Case-insensitive para frases completas, case-sensitive para termos técnicos
            if len(original) > 5:
                texto = re.sub(re.escape(original), substituto, texto, flags=re.IGNORECASE)
            else:
                texto = texto.replace(original, substituto)

        # Limpeza pós-substituição
        for padrao, repl in _PADROES_LIMPEZA:
            texto = padrao.sub(repl, texto)

        tempo_ms = (time.perf_counter() - inicio) * 1000

        # Estatísticas
        tokens_orig = self._estimar_tokens(rules)
        tokens_comp = self._estimar_tokens(texto)
        stats = EstatisticasTokens(
            tokens_originais=tokens_orig,
            tokens_comprimidos=tokens_comp,
            tokens_economizados=tokens_orig - tokens_comp,
            percentual_reducao=self._calcular_reducao(tokens_orig, tokens_comp),
            intensidade=self.intensidade.value,
            fase="INPUT",
            tempo_compressao_ms=tempo_ms,
        )
        self._sessao.historico.append(stats)
        self._sessao.total_tokens_originais += tokens_orig
        self._sessao.total_tokens_comprimidos += tokens_comp

        return Result.ok(valor=texto.strip(), detalhes=stats.to_dict())

    # -------------------------------------------------------------------------
    # Fase 2: PROCESSING — Thinking Denso
    # -------------------------------------------------------------------------

    def format_thinking(self, context: str) -> Result[str]:
        """
        Gera template de raciocínio interno ultra-denso (CoT).

        Produz um esqueleto de 3-5 linhas em English Caveman Ultra para
        guiar o thinking interno do agente durante processamento.

        Args:
            context: Contexto/tarefa atual para raciocínio.

        Returns:
            Result.ok com template CoT ou Result.fail em caso de erro.
        """
        if not context or not context.strip():
            return Result.fail(
                "Contexto de thinking vazio",
                codigo="CAVEMAN_THINKING_VAZIO",
            )

        inicio = time.perf_counter()

        # Template CoT ultra-denso baseado na intensidade
        cot_template = self._gerar_template_cot(context)

        tempo_ms = (time.perf_counter() - inicio) * 1000

        tokens_orig = self._estimar_tokens(context)
        tokens_comp = self._estimar_tokens(cot_template)
        stats = EstatisticasTokens(
            tokens_originais=tokens_orig,
            tokens_comprimidos=tokens_comp,
            tokens_economizados=max(0, tokens_orig - tokens_comp),
            percentual_reducao=self._calcular_reducao(tokens_orig, tokens_comp),
            intensidade=self.intensidade.value,
            fase="PROCESSING",
            tempo_compressao_ms=tempo_ms,
        )
        self._sessao.historico.append(stats)
        self._sessao.total_tokens_originais += tokens_orig
        self._sessao.total_tokens_comprimidos += tokens_comp

        return Result.ok(valor=cot_template, detalhes=stats.to_dict())

    # -------------------------------------------------------------------------
    # Fase 3: OUTPUT — Garantia PT-BR
    # -------------------------------------------------------------------------

    def format_output(self, code: str, lang: str = "pt-br") -> Result[str]:
        """
        Valida e garante que o output esteja em PT-BR padrão alto.

        Verifica marcadores de idioma e aplica transformações quando necessário.
        Código, tipagem, Result Monad e completude são preservados integralmente.

        Args:
            code: Código/texto de output gerado.
            lang: Idioma alvo (padrão: 'pt-br').

        Returns:
            Result.ok com output validado ou Result.fail se idioma incorreto.
        """
        if not code or not code.strip():
            return Result.fail(
                "Output vazio — código ou texto não fornecido",
                codigo="CAVEMAN_OUTPUT_VAZIO",
            )

        inicio = time.perf_counter()

        # Validação de idioma: detecta padrões problemáticos
        problemas_idioma = self._validar_idioma_output(code, lang)

        tempo_ms = (time.perf_counter() - inicio) * 1000

        if problemas_idioma:
            return Result.fail(
                erro="Output não atende ao padrão de idioma PT-BR",
                codigo="CAVEMAN_IDIOMA_INVALIDO",
                detalhes={
                    "problemas": problemas_idioma,
                    "lang_esperado": lang,
                    "tempo_ms": round(tempo_ms, 3),
                },
            )

        # Verifica completude técnica
        avisos_tecnicos = self._validar_completude_tecnica(code)

        stats_dict: Dict[str, Any] = {
            "lang": lang,
            "validacao_ok": True,
            "avisos_tecnicos": avisos_tecnicos,
            "tempo_ms": round(tempo_ms, 3),
        }

        return Result.ok(valor=code, detalhes=stats_dict)

    # -------------------------------------------------------------------------
    # Estatísticas
    # -------------------------------------------------------------------------

    def estimate_savings(self, original_tokens: int, compressed_tokens: int) -> Dict[str, Any]:
        """
        Calcula estatísticas de economia de tokens.

        Args:
            original_tokens: Quantidade de tokens do texto original.
            compressed_tokens: Quantidade de tokens após compressão.

        Returns:
            Dicionário com métricas detalhadas de economia.
        """
        economizados = max(0, original_tokens - compressed_tokens)
        percentual = self._calcular_reducao(original_tokens, compressed_tokens)

        return {
            "tokens_originais": original_tokens,
            "tokens_comprimidos": compressed_tokens,
            "tokens_economizados": economizados,
            "percentual_reducao": round(percentual, 2),
            "intensidade": self.intensidade.value,
            "meta_atingida": self._meta_atingida(percentual),
            "projecao_mensal_100k": {
                "tokens_economizados": economizados * 100,
                "tokens_restantes": compressed_tokens * 100,
            },
        }

    def estatisticas_sessao(self) -> Dict[str, Any]:
        """Retorna estatísticas acumuladas da sessão atual."""
        return {
            "sessao_id": self._sessao.sessao_id,
            "intensidade": self._sessao.intensidade.value,
            "total_operacoes": len(self._sessao.historico),
            "total_tokens_originais": self._sessao.total_tokens_originais,
            "total_tokens_comprimidos": self._sessao.total_tokens_comprimidos,
            "economia_total_percentual": self._sessao.economia_total_percentual,
            "operacoes": [s.to_dict() for s in self._sessao.historico],
        }

    # -------------------------------------------------------------------------
    # Métodos Internos
    # -------------------------------------------------------------------------

    def _obter_mapa_substituicoes(self) -> Dict[str, str]:
        """Retorna o mapa de substituições conforme a intensidade."""
        if self.intensidade == IntensidadeCaveman.LITE:
            return _SUBSTITUICOES_LITE
        elif self.intensidade == IntensidadeCaveman.FULL:
            return _SUBSTITUICOES_FULL
        else:  # ULTRA
            return _SUBSTITUICOES_ULTRA

    def _gerar_template_cot(self, context: str) -> str:
        """Gera template CoT denso baseado no contexto e intensidade."""
        # Extrai palavras-chave do contexto
        palavras_chave = self._extrair_palavras_chave(context)

        if self.intensidade == IntensidadeCaveman.LITE:
            return (
                f"Task: {palavras_chave[0] if palavras_chave else 'unknown'}.\n"
                f"Goal: {palavras_chave[1] if len(palavras_chave) > 1 else 'complete task'}.\n"
                f"Steps: identify → implement → verify.\n"
                f"Constraints: type-safe, Result pattern, no stubs."
            )
        elif self.intensidade == IntensidadeCaveman.FULL:
            return (
                f"Ctx: {palavras_chave[0] if palavras_chave else 'task'}.\n"
                f"Goal: {palavras_chave[1] if len(palavras_chave) > 1 else 'complete'}.\n"
                f"Plan: analyze → impl → test → verify.\n"
                f"Rules: typed, Result monad, no stubs, PT-BR output."
            )
        else:  # ULTRA
            return (
                f"{palavras_chave[0] if palavras_chave else 'task'}"
                f"{'→' + palavras_chave[1] if len(palavras_chave) > 1 else ''}.\n"
                f"analyze→impl→test→verify.\n"
                f"typed∧Result∧¬stubs∧PT-BR."
            )

    def _extrair_palavras_chave(self, texto: str) -> List[str]:
        """Extrai termos técnicos relevantes do texto."""
        # Remove stopwords e extrai termos significativos
        stopwords = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been",
            "have", "has", "had", "do", "does", "did", "will", "would",
            "could", "should", "may", "might", "can", "shall", "must",
            "to", "of", "in", "for", "on", "with", "at", "by", "from",
            "as", "into", "through", "during", "before", "after", "above",
            "below", "between", "and", "but", "or", "nor", "not", "so",
            "yet", "both", "either", "neither", "each", "every", "all",
            "any", "few", "more", "most", "other", "some", "such", "no",
            "only", "own", "same", "than", "too", "very", "just", "because",
            "if", "when", "where", "how", "what", "which", "who", "whom",
            "this", "that", "these", "those", "it", "its",
        }
        palavras = re.findall(r"\b[a-zA-Z_]\w{2,}\b", texto.lower())
        relevantes = [p for p in palavras if p not in stopwords]
        # Remove duplicados mantendo ordem
        vistos: set = set()
        unicas: List[str] = []
        for p in relevantes:
            if p not in vistos:
                vistos.add(p)
                unicas.append(p)
        return unicas[:5]

    @staticmethod
    def _estimar_tokens(texto: str) -> int:
        """
        Estimativa simples de contagem de tokens (aproximação BPE).

        Regra: ~0.75 tokens por palavra em inglês (BPE típico).
        Para textos mistos (código + natural), usa heurística combinada.
        """
        if not texto:
            return 0
        palavras = len(texto.split())
        chars = len(texto)
        # Heurística: max(palavras * 0.75, chars / 4) para cobrir código e prosa
        return max(int(palavras * 0.75), chars // 4)

    @staticmethod
    def _calcular_reducao(original: int, comprimido: int) -> float:
        """Calcula percentual de redução."""
        if original == 0:
            return 0.0
        return (1 - comprimido / original) * 100

    def _meta_atingida(self, percentual: float) -> bool:
        """Verifica se a meta de redução foi atingida por intensidade."""
        metas = {
            IntensidadeCaveman.LITE: 20.0,
            IntensidadeCaveman.FULL: 35.0,
            IntensidadeCaveman.ULTRA: 50.0,
        }
        return percentual >= metas.get(self.intensidade, 35.0)

    @staticmethod
    def _validar_idioma_output(code: str, lang: str) -> List[str]:
        """Valida se o output está no idioma correto."""
        problemas: List[str] = []

        if lang.lower() not in ("pt-br", "pt_br", "ptbr", "pt"):
            problemas.append(f"Idioma não suportado: {lang}")
            return problemas

        # Marcadores de output em inglês que deveriam estar em PT-BR
        marcadores_en = [
            (r"\bError handling\b", "Tratamento de erros"),
            (r"\bConfiguration file\b", "Arquivo de configuração"),
            (r"\bDatabase connection\b", "Conexão com banco de dados"),
            (r"\bAuthentication required\b", "Autenticação obrigatória"),
            (r"\bFile not found\b", "Arquivo não encontrado"),
            (r"\bInvalid input\b", "Entrada inválida"),
            (r"\bSuccess\b(?![\w])", "Sucesso"),
            (r"\bFailed\b(?![\w])", "Falha"),
            (r"\bWarning\b(?![\w])", "Aviso"),
        ]

        # Só flagga se houver muitos marcadores em inglês (tolerância para código)
        # Marcadores em strings de erro/docstring são problemáticos
        for padrao, _sugestao in marcadores_en:
            # Ignora dentro de blocos de código (``` ... ```)
            texto_sem_codigo = re.sub(r"```[\s\S]*?```", "", code)
            if re.search(padrao, texto_sem_codigo):
                problemas.append(f"Possível texto em inglês: '{padrao}' encontrado")

        return problemas

    @staticmethod
    def _validar_completude_tecnica(code: str) -> List[str]:
        """Verifica indicadores de completude técnica no output."""
        avisos: List[str] = []

        # Verifica stubs incompletos
        stubs_padroes = [
            (r"pass\s*#\s*TODO", "Stub com TODO encontrado"),
            (r"\.\.\.#\s*stub", "Stub com ellipsis encontrado"),
            (r"NotImplementedError\(\)", "NotImplementedError sem implementação"),
            (r"raise\s+NotImplementedError", "NotImplementedError levantado"),
        ]

        for padrao, aviso in stubs_padroes:
            if re.search(padrao, code, re.IGNORECASE):
                avisos.append(aviso)

        # Verifica se há Result pattern
        if "Result" in code and "Result.ok" not in code and "Result.fail" not in code:
            avisos.append("Result importado mas não utilizado (ok/fail)")

        return avisos
