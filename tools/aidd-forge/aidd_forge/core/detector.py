"""Diagnostico de SO e auto-descoberta da frota de agentes instalados no host.

Busca silenciosa (nunca lanca excecao, nunca escreve em stdout/stderr) via
`shutil.which`, que ja abstrai `which` (POSIX) e `Get-Command` (Windows)
atras de uma unica API portavel.
"""

from __future__ import annotations

import platform
import shutil
from dataclasses import dataclass

KNOWN_TOOLS: tuple[str, ...] = ("claude", "codex", "agy", "cursor", "ollama")
ORCA_EXECUTABLE = "orca"


@dataclass(frozen=True)
class HostReport:
    """Retrato do host: SO, frota de agentes disponiveis e presenca do ORCA."""

    os_name: str
    available_tools: tuple[str, ...]
    orca_present: bool

    @property
    def has_single_agent(self) -> bool:
        return len(self.available_tools) == 1

    @property
    def has_no_agent(self) -> bool:
        return len(self.available_tools) == 0


def detect_os() -> str:
    """Normaliza `platform.system()` para windows/darwin/linux."""
    system = platform.system().lower()
    if system.startswith("win"):
        return "windows"
    if system == "darwin":
        return "darwin"
    return "linux"


def detect_fleet(tools: tuple[str, ...] = KNOWN_TOOLS) -> tuple[str, ...]:
    """Busca silenciosa por executaveis conhecidos via `shutil.which`."""
    return tuple(tool for tool in tools if shutil.which(tool) is not None)


def detect_orca() -> bool:
    """Verifica se o binario `orca` esta disponivel no PATH."""
    return shutil.which(ORCA_EXECUTABLE) is not None


def detect_host() -> HostReport:
    """Executa o diagnostico completo do host (SO + frota + ORCA)."""
    return HostReport(
        os_name=detect_os(),
        available_tools=detect_fleet(),
        orca_present=detect_orca(),
    )
