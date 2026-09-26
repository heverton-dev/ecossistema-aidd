"""Plan parser for ORCA ADE orchestration.

Parses a plan folder containing 00-PROCESSO-E-DECISOES.md + NN-<name>.md
files and returns structured front data.

Zero LLM cost — pure deterministic parsing.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Front:
    """A single execution front extracted from a plan folder."""

    name: str
    file_path: Path
    content: str
    index: int
    prompt: str = ""


@dataclass
class Plan:
    """Parsed plan: master context + list of fronts."""

    folder: Path
    master_file: Path
    master_content: str
    fronts: list[Front] = field(default_factory=list)

    @property
    def front_count(self) -> int:
        return len(self.fronts)

    @property
    def identificador(self) -> str:
        """`PLAN-0016` — identificador global da iniciativa."""
        return identificador_do_plano(self.folder)

    def rotulo(self, front: "Front") -> str:
        """`PLAN-0016-fase-04-eliminar-timesleep` — nome da mesa desta frente."""
        return rotulo_da_frente(self.identificador, front.index, front.name)


_FRONT_PATTERN = re.compile(r"^(\d{2})-(.+)\.md$")

_ID_PLANO_PATTERN = re.compile(r"^(PLAN-\d{4})[-_]")


def identificador_do_plano(pasta: Path) -> str:
    """`PLAN-0016` a partir de `PLAN-0016-qualidade-testes-mutacao`.

    Planos legados (sem o prefixo) e pastas de teste caem no nome da pasta
    mesmo — o rotulo continua util, so nao fica numerado.
    """
    achado = _ID_PLANO_PATTERN.match(pasta.name)
    return achado.group(1) if achado else pasta.name


_PALAVRAS_IGNORADAS_ROTULO = {
    "e", "de", "da", "do", "das", "dos", "para", "com", "sem", "a", "o", "as",
    "os", "em", "no", "na", "nos", "nas", "ao", "aos", "por", "pos", "the",
}


def rotulo_da_frente(identificador: str, indice: int, nome: str, palavras: int = 3) -> str:
    """`PLAN-0016-fase-04-eliminar-timesleep-injetar`.

    A fase leva dois digitos de proposito: com um so, `fase-10` apareceria
    antes de `fase-2` em qualquer lista ordenada por nome.

    O nome do item entra cortado em 3 palavras significativas — mesmo limite
    das pastas de plano. Sem o corte o rotulo chega a 70 caracteres, e ele vira
    nome de pasta de worktree e de branch: caminho longo demais quebra no
    Windows e fica ilegivel no painel de mesas.
    """
    partes = [p for p in nome.split("-") if p and p not in _PALAVRAS_IGNORADAS_ROTULO]
    curto = "-".join(partes[:palavras]) or nome
    return f"{identificador}-fase-{indice:02d}-{curto}"

_MASTER_FILENAME = "00-PROCESSO-E-DECISOES.md"

# Section headers vary across plans generated at different times (with/without
# Portuguese accents - e.g. "Definicao"/"Definição"). Patterns below tolerate
# both so extraction works on every existing plan, not just new ones.
_RE_ESCOPO = re.compile(r"^> \*\*Escopo:\*\*.*$", re.MULTILINE)
_RE_DEFINICAO_PRONTO = re.compile(
    r"^## Defini[cç][aã]o de Pronto\s*$(.*?)(?=^## |\Z)", re.MULTILINE | re.DOTALL
)
_RE_CRITERIO_SAIDA = re.compile(
    r"^## Crit[eé]rio de sa[ií]da\s*$(.*?)(?=^## |\Z)", re.MULTILINE | re.DOTALL
)
_RE_PROMPT_INGLES = re.compile(
    r"^## Prompt de Execu[cç][aã]o.*English version\s*$.*?^(`{1,3})[a-zA-Z]*\s*$\n(.*?)\n^\1\s*$",
    re.MULTILINE | re.DOTALL,
)


def extrair_prompt_executor(conteudo: str) -> str:
    """Builds the actual prompt sent to the executor: Scope + Definition of
    Done + Exit Criteria (the minimum context the English block may refer to
    as "above") + the English execution block itself - never the whole raw
    file, which today duplicates the same instruction in Portuguese and adds
    narrative context the executor doesn't need (real token waste).

    Falls back to the full raw content when the file doesn't have the
    expected sections (older/non-standard format) - this must never break
    orchestration, only optimize it when the shape is recognized.
    """
    m_dod = _RE_DEFINICAO_PRONTO.search(conteudo)
    m_prompt = _RE_PROMPT_INGLES.search(conteudo)
    if not (m_dod and m_prompt):
        return conteudo

    partes = []
    m_escopo = _RE_ESCOPO.search(conteudo)
    if m_escopo:
        partes.append(m_escopo.group(0).replace("> **Escopo:**", "Scope:").strip())

    partes.append("Definition of Done:")
    partes.append(m_dod.group(1).strip())

    m_exit = _RE_CRITERIO_SAIDA.search(conteudo)
    if m_exit:
        partes.append("Exit Criteria:")
        partes.append(m_exit.group(1).strip())

    partes.append(m_prompt.group(2).strip())
    return "\n\n".join(partes)


def _is_front_file(filename: str) -> tuple[bool, int, str]:
    """Check if a filename matches the NN-<name>.md pattern.

    The master file (00-PROCESSO-E-DECISOES.md) is explicitly excluded.
    Returns (is_match, index, name).
    """
    if filename == _MASTER_FILENAME:
        return False, 0, ""
    m = _FRONT_PATTERN.match(filename)
    if m:
        return True, int(m.group(1)), m.group(2)
    return False, 0, ""


def parse_plan(folder: str | Path) -> Plan:
    """Parse a plan folder and return structured front data.

    Args:
        folder: Path to the plan directory (relative, absolute, or ".").

    Returns:
        Plan object with master context and list of Front objects.

    Raises:
        FileNotFoundError: If folder or 00-PROCESSO-E-DECISOES.md not found.
        ValueError: If folder contains no NN-*.md front files.
    """
    folder_path = Path(folder).resolve()

    if not folder_path.is_dir():
        raise FileNotFoundError(f"Plan folder not found: {folder_path}")

    master_path = folder_path / "00-PROCESSO-E-DECISOES.md"
    if not master_path.is_file():
        raise FileNotFoundError(
            f"Master file 00-PROCESSO-E-DECISOES.md not found in {folder_path}"
        )

    master_content = master_path.read_text(encoding="utf-8")

    fronts: list[Front] = []
    for entry in sorted(folder_path.iterdir()):
        if not entry.is_file():
            continue
        is_match, index, name = _is_front_file(entry.name)
        if is_match:
            content = entry.read_text(encoding="utf-8")
            fronts.append(
                Front(
                    name=name, file_path=entry, content=content, index=index,
                    prompt=extrair_prompt_executor(content),
                )
            )

    if not fronts:
        raise ValueError(
            f"No NN-*.md front files found in {folder_path}"
        )

    return Plan(
        folder=folder_path,
        master_file=master_path,
        master_content=master_content,
        fronts=fronts,
    )
