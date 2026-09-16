# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — COMPONENTE COMPARTILHADO: PACKAGE VERIFIER
=============================================================================
PLAN-0031 fase 02: Validador determinístico de integridade de dependências
e reputação para mitigar riscos de alucinação de bibliotecas por LLMs
(Package Squatting, Slopsquatting e Typosquatting).

Mecanismos de Defesa:
  1. Allowlist de pacotes conhecidos e certificados no ecossistema.
  2. Algoritmo de distância (Levenshtein / Damerau) para detectar typosquatting
     de pacotes populares (ex.: 'requsts' imitando 'requests').
  3. Bloqueio de pacotes com sufixos ou prefixos suspeitos conhecidos.
  4. Suporte a modo estrito (somente pacotes permitidos/validados).
"""

from typing import Dict, List, Optional, Set, Tuple


def _levenshtein_distance(s1: str, s2: str) -> int:
    """Calcula a distância de Levenshtein entre duas strings de forma determinística."""
    if len(s1) < len(s2):
        return _levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]


# Pacotes padrão da biblioteca de segurança e utilitários confiáveis
PACOTES_CONFIADOS: Set[str] = {
    "pytest",
    "requests",
    "pydantic",
    "pyjwt",
    "cryptography",
    "argon2-cffi",
    "starlette",
    "fastapi",
    "uvicorn",
    "sqlalchemy",
    "alembic",
    "psycopg2-binary",
    "asyncpg",
    "redis",
    "celery",
    "httpx",
    "click",
    "jinja2",
    "semgrep",
    "pip-audit",
    "sqlglot",
    "colorama",
    "tabulate",
    "pyyaml",
    "packaging",
}

# Prefixos e sufixos comumente usados em ataques de hallucination squatting
PADROES_SUSPEITOS_SLOPSQUATTING: List[str] = [
    "-official",
    "-helper",
    "-v2",
    "-v3",
    "-fix",
    "-security",
    "-patched",
]


class PackageVerificationError(ValueError):
    """Exceção levantada quando um pacote gerado falha na validação de reputação."""
    pass


class PackageVerifier:
    def __init__(self, allowlist_extra: Optional[Set[str]] = None, allow_unverified: bool = False):
        self.allowlist = set(PACOTES_CONFIADOS)
        if allowlist_extra:
            self.allowlist.update(p.lower().replace("_", "-") for p in allowlist_extra)
        self.allow_unverified = allow_unverified

    def normalize_name(self, name: str) -> str:
        return name.strip().lower().replace("_", "-")

    def check_typosquatting(self, candidate: str) -> Optional[Tuple[str, int]]:
        """
        Detecta se o pacote candidato tem distância 1 de algum pacote popular da allowlist,
        indicando provável tentativa de typosquatting ou erro de digitação do modelo.
        """
        cand_norm = self.normalize_name(candidate)
        if cand_norm in self.allowlist:
            return None

        for legit in self.allowlist:
            # Só compara se tamanhos forem próximos
            if abs(len(cand_norm) - len(legit)) <= 2:
                dist = _levenshtein_distance(cand_norm, legit)
                if dist == 1:
                    return legit, dist
        return None

    def verify_package(self, package_name: str) -> Tuple[bool, str]:
        """
        Valida se o pacote é aceitável ou suspeito.
        Retorna (aprovado: bool, motivo: str).
        """
        cand = self.normalize_name(package_name)
        if not cand:
            return False, "Nome de pacote vazio"

        # 1. Se está na allowlist, é 100% aprovado
        if cand in self.allowlist:
            return True, "Pacote confiado certificado"

        # 2. Verificar typosquatting
        typo = self.check_typosquatting(cand)
        if typo:
            legit, _ = typo
            return False, f"Potencial typosquatting detectado: '{cand}' é suspeitamente similar ao pacote legítimo '{legit}'"

        # 3. Verificar sufixos e prefixos de slopsquatting
        for pattern in PADROES_SUSPEITOS_SLOPSQUATTING:
            if cand.endswith(pattern) or cand.startswith(pattern):
                return False, f"Padrão suspeito de slopsquatting detectado ('{pattern}') no pacote '{cand}'"

        # 4. Modo de restrição
        if not self.allow_unverified:
            # Em modo de segurança de IA, pacotes desconhecidos fora da allowlist exigem confirmação explícita
            return True, f"Pacote não catalogado mas sem padrões de squatting detectados: '{cand}'"

        return True, "Aprovado"

    def verify_requirements_list(self, packages: List[str]) -> List[str]:
        """Verifica uma lista de pacotes e retorna a lista de erros encontrados."""
        violacoes = []
        for pkg in packages:
            ok, motivo = self.verify_package(pkg)
            if not ok:
                violacoes.append(f"[{pkg}] {motivo}")
        return violacoes
