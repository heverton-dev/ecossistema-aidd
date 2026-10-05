"""Provedor de micro-ambientes granulares por fase (Phase-Level Agentic Fencing).

Cada fase do pipeline recebe sua propria arvore isolada em
`.aidd/pipeline/phase_XX_nome/`, com um `AGENTS.md` cirurgico (~380 tokens)
e um `mcp_config.json` exclusivo: nenhuma fase enxerga regras ou MCPs de
outra fase. Reaproveita o motor deterministico do `Injector` (copia pura,
zero LLM) para instanciar os templates de `templates/pipeline_phases/`
dentro do projeto alvo.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from aidd_forge.core.injector import InjectionResult, Injector

PIPELINE_SUBDIR = Path(".aidd") / "pipeline"

# Todo micro-ambiente de fase precisa destes dois arquivos para ser valido.
REQUIRED_PHASE_FILES: tuple[str, ...] = ("AGENTS.md", "mcp_config.json")


@dataclass(frozen=True)
class PhaseFenceResult:
    """Resumo da provisao dos micro-ambientes de fase."""

    phases: tuple[str, ...]
    injection: InjectionResult


class PhaseFencer:
    """Provisiona `.aidd/pipeline/phase_XX_*/` dentro do projeto alvo."""

    def __init__(self, templates_root: Path, target_root: Path, force: bool = False):
        self.templates_root = Path(templates_root)
        self.target_root = Path(target_root)
        self.force = force

    def run(self) -> PhaseFenceResult:
        """Copia cada fase de `templates_root/pipeline_phases` para o alvo."""
        source = self.templates_root / "pipeline_phases"
        if not source.exists():
            raise FileNotFoundError(f"templates de fases nao encontrados: {source}")

        destination = self.target_root / PIPELINE_SUBDIR
        injector = Injector(source, destination, force=self.force)
        injection = injector.run()

        phases = self._provisioned_phases(destination)
        return PhaseFenceResult(phases=phases, injection=injection)

    def _provisioned_phases(self, destination: Path) -> tuple[str, ...]:
        """Confere que cada fase provisionada tem AGENTS.md e mcp_config.json."""
        phase_dirs = sorted(p.name for p in destination.iterdir() if p.is_dir())
        for phase in phase_dirs:
            for required in REQUIRED_PHASE_FILES:
                if not (destination / phase / required).exists():
                    raise FileNotFoundError(
                        f"fase '{phase}' incompleta: falta '{required}' em "
                        f"{destination / phase}"
                    )
        return tuple(phase_dirs)
