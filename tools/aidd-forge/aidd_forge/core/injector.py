"""Motor deterministico de injecao de arquivos e symlinks do AIDD Forge.

Copia a arvore de templates de governanca para o projeto alvo sem acionar
nenhum LLM (mecanica pura, custo zero de tokens). Arquivos ja existentes no
alvo nunca sao sobrescritos a menos que `force=True` seja passado, para
preservar edicoes do usuario.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path

from aidd_forge.core.harness_manifest import (
    carregar_skill_dirs_canonicos,
    carregar_skill_overrides_canonicos,
)


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

    def mirror_skills_all_harnesses(
        self, skills_subdir: str = "skills"
    ) -> InjectionResult:
        """Espelha as skills em TODAS as pastas de harness do manifesto canonico
        (alem de .agent/skills/ ja feito por link_skills).

        Achado real (2026-09-15): antes desta correcao, so mirava
        `.claude/skills/` e `.gemini/skills/` (faltavam Antigravity, OpenCode,
        MimoCode, Cursor, CodeBuddy), e a copia pro Gemini CLI usava o formato
        errado (SKILL.md solto — Gemini CLI so le o formato de extensions).
        Agora le `aidd_forge.core.harness_manifest` (mesma fonte usada por
        `sincronizar_skill`/`sincronizar_command`), nunca lista propria.
        """
        result = InjectionResult()
        skills_root = self.target_root / skills_subdir
        if not skills_root.exists():
            return result

        skill_dirs = [
            p for p in sorted(skills_root.iterdir()) if p.is_dir() and (p / "SKILL.md").exists()
        ]
        if not skill_dirs:
            return result

        for rel_harness in carregar_skill_dirs_canonicos():
            target_harness_root = self.target_root / rel_harness
            target_harness_root.mkdir(parents=True, exist_ok=True)

            for skill_dir in skill_dirs:
                self._copiar_skill(skill_dir, target_harness_root / skill_dir.name, result)

        gemini_override = carregar_skill_overrides_canonicos().get("gemini-cli")
        if gemini_override is not None:
            for skill_dir in skill_dirs:
                nome = skill_dir.name
                link_path = self.target_root / gemini_override.dest_dir_template.replace(
                    "{nome}", nome
                )
                self._copiar_skill(skill_dir, link_path, result)

                if (
                    gemini_override.manifesto_extra_path_template
                    and gemini_override.manifesto_extra_conteudo_template
                ):
                    extra_path = self.target_root / gemini_override.manifesto_extra_path_template.replace(
                        "{nome}", nome
                    )
                    if not extra_path.exists() or self.force:
                        conteudo = {
                            chave: (valor.replace("{nome}", nome) if isinstance(valor, str) else valor)
                            for chave, valor in gemini_override.manifesto_extra_conteudo_template.items()
                        }
                        extra_path.parent.mkdir(parents=True, exist_ok=True)
                        extra_path.write_text(
                            json.dumps(conteudo, indent=2, ensure_ascii=False) + "\n",
                            encoding="utf-8",
                        )
                        result.created.append(extra_path)

        return result

    def _copiar_skill(self, skill_dir: Path, link_path: Path, result: InjectionResult) -> None:
        """Copia (nao symlink — precisa sobreviver em runners que nao trazem o
        template original) uma skill pra `link_path`, registrando o resultado."""
        if link_path.exists() or link_path.is_symlink():
            if not self.force:
                result.skipped.append(link_path)
                return
            if link_path.is_symlink() or link_path.is_file():
                link_path.unlink()
            else:
                shutil.rmtree(link_path)
            result.overwritten.append(link_path)
        else:
            result.created.append(link_path)

        shutil.copytree(skill_dir, link_path)

