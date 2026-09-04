# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD v5.1 Zero Friction — Intent Router
=============================================================================
Converte linguagem natural em comandos AIDD estruturados.
Camada de interface zero-friction: o usuário fala português, o sistema executa.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class IntentPattern:
    """Padrão de correspondência para intenção do usuário."""

    action: str
    regex: re.Pattern[str]
    module_group: Optional[int] = None  # índice do grupo regex que contém módulos
    default_options: Dict[str, Any] = field(default_factory=dict)
    description: str = ""


@dataclass
class IntentResult:
    """Resultado do parsing de intenção."""

    action: str
    modules: List[str]
    options: Dict[str, Any]
    match_confidence: float
    raw_text: str
    pattern_description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action,
            "modules": self.modules,
            "options": self.options,
            "match_confidence": self.match_confidence,
            "raw_text": self.raw_text,
        }


# ---------------------------------------------------------------------------
# Padrões de intenção pré-definidos
# ---------------------------------------------------------------------------

_PATTERNS: List[IntentPattern] = [
    # Compose / arquitetura corporativa
    IntentPattern(
        action="compose",
        regex=re.compile(
            r"arquitetura\s+corporativa\s+para\s+(.+)",
            re.IGNORECASE,
        ),
        module_group=1,
        default_options={"role": "architect"},
        description="Arquitetura corporativa com papel de arquiteto",
    ),
    # Compose explícito com módulos
    IntentPattern(
        action="compose",
        regex=re.compile(
            r"compose\s+(.+)",
            re.IGNORECASE,
        ),
        module_group=1,
        default_options={},
        description="Compose com módulos explícitos",
    ),
    # Criar módulo
    IntentPattern(
        action="add-module",
        regex=re.compile(
            r"criar\s+m[oó]dulo\s+(.+)",
            re.IGNORECASE,
        ),
        module_group=1,
        default_options={},
        description="Criação de novo módulo vertical slice",
    ),
    # Testar tudo
    IntentPattern(
        action="test",
        regex=re.compile(
            r"testar?\s+tudo|rodar?\s+testes?|executar?\s+testes?",
            re.IGNORECASE,
        ),
        default_options={"scope": "all"},
        description="Executar suíte completa de testes",
    ),
    # Testar tipo específico
    IntentPattern(
        action="test",
        regex=re.compile(
            r"testar?\s+(unit[aá]ri[oa]s?|contratos?|load|carga|integra[cç][aã]o)",
            re.IGNORECASE,
        ),
        module_group=1,
        default_options={},
        description="Executar testes de tipo específico",
    ),
    # Deploy
    IntentPattern(
        action="deploy",
        regex=re.compile(
            r"fazer?\s+deploy|deploy(?:\s+(?:docker|vps|produ[cç][aã]o))?",
            re.IGNORECASE,
        ),
        default_options={},
        description="Deploy do projeto",
    ),
    # Auditoria de segurança
    IntentPattern(
        action="audit",
        regex=re.compile(
            r"auditar?\s+seguran[çc]a|audit(?:ar)?\s+seguran[çc]a|seguran[çc]a\s+audit",
            re.IGNORECASE,
        ),
        default_options={"report": True},
        description="Auditoria de segurança completa",
    ),
    # Status do projeto
    IntentPattern(
        action="status",
        regex=re.compile(
            r"status\s+do\s+projeto|como\s+est[aá]\s+o\s+projeto|status",
            re.IGNORECASE,
        ),
        default_options={},
        description="Status geral do projeto",
    ),
    # Auto-fix
    IntentPattern(
        action="fix",
        regex=re.compile(
            r"auto[\s-]?fix|corrigir?\s+tudo|consertar?\s+tudo|fix",
            re.IGNORECASE,
        ),
        default_options={},
        description="Auto-correção de problemas",
    ),
    # Gates
    IntentPattern(
        action="gates",
        regex=re.compile(
            r"rodar?\s+gate[s]?\s*(.+)?|executar?\s+gate[s]?\s*(.+)?|gates?\s*(.+)?",
            re.IGNORECASE,
        ),
        module_group=1,
        default_options={},
        description="Execução de gates mecânicos",
    ),
]


def _extract_modules(raw: Optional[str]) -> List[str]:
    """Extrai lista de módulos de uma string bruta.

    Suporta separadores: vírgula, 'e', '+', espaço.
    """
    if not raw:
        return []

    text = raw.strip().strip("\"'")
    # Normaliza separadores
    text = re.sub(r"\s*[+,]\s*", " ", text)
    parts = re.split(r"\s+e\s+|\s+", text, flags=re.IGNORECASE)
    modules = [p.strip().lower() for p in parts if p.strip()]
    # Remove artigos/preposições que possam ter escapado
    stopwords = {"o", "a", "os", "as", "de", "do", "da", "dos", "das", "em", "no", "na"}
    return [m for m in modules if m not in stopwords]


def _normalize_deploy_target(text: str) -> Optional[str]:
    """Detecta alvo de deploy na string."""
    lower = text.lower()
    if "docker" in lower:
        return "docker"
    if "vps" in lower:
        return "vps"
    if "produção" in lower or "producao" in lower:
        return "production"
    return None


def _normalize_test_scope(text: str) -> str:
    """Detecta escopo de teste na string."""
    lower = text.lower()
    if "unit" in lower or "unitári" in lower:
        return "unit"
    if "contrat" in lower:
        return "contracts"
    if "load" in lower or "carga" in lower:
        return "load"
    if "integraç" in lower or "integrac" in lower:
        return "integration"
    return "all"


class IntentRouter:
    """Roteador de intenções que converte linguagem natural em comandos AIDD.

    Uso::

        router = IntentRouter()
        result = router.parse_intent("criar modulo pagamentos")
        # result.action == "add-module"
        # result.modules == ["pagamentos"]
    """

    def __init__(self, extra_patterns: Optional[List[IntentPattern]] = None):
        self._patterns: List[IntentPattern] = list(_PATTERNS)
        if extra_patterns:
            self._patterns.extend(extra_patterns)

    def parse_intent(self, text: str) -> Dict[str, Any]:
        """Converte texto em comando AIDD estruturado.

        Args:
            text: Texto em linguagem natural (PT-BR ou comandos slash).

        Returns:
            Dicionário com ``action``, ``modules``, ``options`` e
            ``match_confidence``.
        """
        result = self._match(text)
        return result.to_dict()

    def parse_intent_result(self, text: str) -> IntentResult:
        """Versão que retorna ``IntentResult`` tipado."""
        return self._match(text)

    def _match(self, text: str) -> IntentResult:
        """Tenta casar o texto com cada padrão conhecido."""
        stripped = text.strip()
        if not stripped:
            return IntentResult(
                action="unknown",
                modules=[],
                options={},
                match_confidence=0.0,
                raw_text=text,
            )

        best: Optional[Tuple[IntentPattern, re.Match[str], float]] = None

        for pattern in self._patterns:
            m = pattern.regex.search(stripped)
            if not m:
                continue

            # Calcula confiança baseada em quão específico foi o match
            matched_len = m.end() - m.start()
            coverage = matched_len / max(len(stripped), 1)
            # Padrões mais longos e com maior cobertura = mais confiança
            confidence = min(0.5 + coverage * 0.5, 1.0)

            if best is None or confidence > best[2]:
                best = (pattern, m, confidence)

        if best is None:
            return IntentResult(
                action="unknown",
                modules=[],
                options={},
                match_confidence=0.0,
                raw_text=text,
                pattern_description="Nenhum padrão reconhecido",
            )

        pattern, match, confidence = best

        # Extrai módulos do grupo de captura
        raw_modules = match.group(pattern.module_group) if pattern.module_group else None
        modules = _extract_modules(raw_modules)

        # Constrói options a partir dos defaults
        options = dict(pattern.default_options)

        # Enriquecimentos específicos por ação
        if pattern.action == "deploy":
            target = _normalize_deploy_target(stripped)
            if target:
                options["target"] = target

        if pattern.action == "test":
            scope = _normalize_test_scope(stripped)
            options["scope"] = scope

        return IntentResult(
            action=pattern.action,
            modules=modules,
            options=options,
            match_confidence=round(confidence, 2),
            raw_text=text,
            pattern_description=pattern.description,
        )

    def add_pattern(self, pattern: IntentPattern) -> None:
        """Registra um novo padrão de intenção em runtime."""
        self._patterns.append(pattern)

    @property
    def known_actions(self) -> List[str]:
        """Lista todas as ações conhecidas pelo router."""
        return list({p.action for p in self._patterns})
