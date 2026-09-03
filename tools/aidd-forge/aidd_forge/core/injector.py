"""Motor deterministico de injecao de arquivos e symlinks do AIDD Forge.

Copia a arvore de templates de governanca para o projeto alvo sem acionar
nenhum LLM (mecanica pura, custo zero de tokens). Arquivos ja existentes no
alvo nunca sao sobrescritos a menos que `force=True` seja passado, para
preservar edicoes do usuario.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class InjectionResult:
    """Resumo de uma execucao de injecao, usado para relatar ao usuario."""

    created: list[Path] = field(default_factory=list)
    overwritten: list[Path] = field(default_factory=list)
    skipped: list[Path] = field(default_factory=list)

    def merge(self, other: "InjectionResult") -> None:
        self.created.extend(other.created)
        self.overwritten.extend(other.overwritten)
        self.skipped.extend(other.skipped)


class Injector:
    """Injeta a arvore de `templates_root` dentro de `target_root`."""

    def __init__(self, templates_root: Path, target_root: Path, force: bool = False):
        self.templates_root = Path(templates_root)
        self.target_root = Path(target_root)
        self.force = force

    def run(self) -> InjectionResult:
        """Copia arquivos e cria diretorios; retorna o que foi feito."""
        if not self.templates_root.exists():
            raise FileNotFoundError(f"templates root nao encontrado: {self.templates_root}")

        result = InjectionResult()
        for src in sorted(self.templates_root.rglob("*")):
            rel = src.relative_to(self.templates_root)
            dst = self.target_root / rel

            if src.is_dir():
                dst.mkdir(parents=True, exist_ok=True)
                continue

            self._inject_file(src, dst, result)

        return result

    def _inject_file(self, src: Path, dst: Path, result: InjectionResult) -> None:
        dst.parent.mkdir(parents=True, exist_ok=True)

        if dst.exists():
            if not self.force:
                result.skipped.append(dst)
                return
            result.overwritten.append(dst)
        else:
            result.created.append(dst)

        shutil.copy2(src, dst)

    def link_ide_rules(self, aliases: dict[str, str]) -> InjectionResult:
        """Cria aliases de regras de IDE apontando para arquivos ja injetados.

        `aliases` mapeia nome do link (ex: "CLAUDE.md") para o caminho
        relativo do arquivo alvo dentro de `target_root` (ex:
        "governance/AGENTS.md"). Usa symlink quando o SO permite; cai para
        copia quando nao (ex: Windows sem modo desenvolvedor/admin).
        """
        result = InjectionResult()
        for alias_name, target_rel in aliases.items():
            link_path = self.target_root / alias_name
            target_path = self.target_root / target_rel

            if not target_path.exists():
                continue

            if link_path.exists() or link_path.is_symlink():
                if not self.force:
                    result.skipped.append(link_path)
                    continue
                link_path.unlink()
                result.overwritten.append(link_path)
            else:
                result.created.append(link_path)

            try:
                link_path.symlink_to(target_path)
            except OSError:
                shutil.copy2(target_path, link_path)

        return result

    def link_skills(
        self, skills_subdir: str = "skills", canonical_dir: str = ".agent/skills"
    ) -> InjectionResult:
        """Vincula cada skill ja injetada em `target_root/<skills_subdir>/<nome>`
        na pasta canonica `target_root/<canonical_dir>/<nome>`.

        Segue o mesmo contrato de `link_ide_rules`: cria symlink de diretorio
        quando o SO permite, com fallback para `copytree` quando nao (ex:
        Windows sem modo desenvolvedor/admin). So vincula diretorios que
        contem `SKILL.md` — pastas sem esse arquivo nao sao skills validas
        e sao ignoradas silenciosamente.
        """
        result = InjectionResult()
        skills_root = self.target_root / skills_subdir
        if not skills_root.exists():
            return result

        canonical_root = self.target_root / canonical_dir
        canonical_root.mkdir(parents=True, exist_ok=True)

        for skill_dir in sorted(p for p in skills_root.iterdir() if p.is_dir()):
            if not (skill_dir / "SKILL.md").exists():
                continue

            link_path = canonical_root / skill_dir.name

            if link_path.exists() or link_path.is_symlink():
                if not self.force:
                    result.skipped.append(link_path)
                    continue
                if link_path.is_symlink() or link_path.is_file():
                    link_path.unlink()
                else:
                    shutil.rmtree(link_path)
                result.overwritten.append(link_path)
            else:
                result.created.append(link_path)

            try:
                link_path.symlink_to(skill_dir, target_is_directory=True)
            except OSError:
                shutil.copytree(skill_dir, link_path)

        return result
