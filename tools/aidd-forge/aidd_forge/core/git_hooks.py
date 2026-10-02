"""Instalador de Git Hooks: blindagem binaria de Quality Gates no `pre-commit`.

Copia os 7 scripts de Quality Gate (`templates/gates/G_*.py`, mecanica pura,
zero LLM) para `<alvo>/gates/` e grava um hook `pre-commit` que executa
cada gate em sequencia. Qualquer gate com `exit 1` bloqueia o commit
(`exit 0` / `exit 1` binario, sem meio-termo). Reaproveita o `Injector`
para a copia dos gates, seguindo o mesmo padrao de `PhaseFencer`.
"""

from __future__ import annotations

import shutil
import stat
from dataclasses import dataclass
from pathlib import Path

from aidd_forge.core.injector import InjectionResult

GATES_SUBDIR = "gates"
HOOK_NAME = "pre-commit"

HOOK_SCRIPT = """#!/usr/bin/env sh
# AIDD Forge - executor binario de Quality Gates (gerado por git_hooks.py).
# Nao editar a mao: reexecute 'forge init --force' para regerar este hook.
set -u

REPO_ROOT="$(git rev-parse --show-toplevel)"
GATES_DIR="$REPO_ROOT/gates"

if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
else
    echo "[aidd-forge] Python nao encontrado no PATH. Commit bloqueado."
    exit 1
fi

STATUS=0
for gate in "$GATES_DIR"/G_*.py; do
    [ -e "$gate" ] || continue
    "$PYTHON_BIN" "$gate" "$REPO_ROOT"
    if [ $? -ne 0 ]; then
        STATUS=1
    fi
done

if [ "$STATUS" -ne 0 ]; then
    echo "[aidd-forge] Quality Gates reprovados. Commit bloqueado."
else
    echo "[aidd-forge] Todos os Quality Gates aprovados."
fi

exit $STATUS
"""


@dataclass(frozen=True)
class GitHooksResult:
    """Resumo da instalacao dos gates e do hook `pre-commit`."""

    gates_injection: InjectionResult
    gate_scripts: tuple[str, ...]
    hook_installed: bool
    hook_path: Path | None
    skipped_reason: str | None


class GitHooksInstaller:
    """Instala os Quality Gates e o hook `pre-commit` binario no projeto alvo."""

    def __init__(self, templates_root: Path, target_root: Path, force: bool = False):
        self.templates_root = Path(templates_root)
        self.target_root = Path(target_root)
        self.force = force

    def run(self) -> GitHooksResult:
        """Copia os gates e grava o hook `pre-commit`; retorna o que foi feito."""
        gates_injection = self._install_gates()
        gate_scripts = self._provisioned_gate_names()

        git_dir = _resolve_git_dir(self.target_root)
        if git_dir is None:
            return GitHooksResult(
                gates_injection=gates_injection,
                gate_scripts=gate_scripts,
                hook_installed=False,
                hook_path=None,
                skipped_reason="'.git' nao encontrado (nao e um repositorio git)",
            )

        hooks_dir = git_dir / "hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)
        hook_path = hooks_dir / HOOK_NAME

        if hook_path.exists() and not self.force:
            return GitHooksResult(
                gates_injection=gates_injection,
                gate_scripts=gate_scripts,
                hook_installed=False,
                hook_path=hook_path,
                skipped_reason=f"'{HOOK_NAME}' ja existe (use --force para sobrescrever)",
            )

        hook_path.write_text(HOOK_SCRIPT, encoding="utf-8", newline="\n")
        _make_executable(hook_path)

        return GitHooksResult(
            gates_injection=gates_injection,
            gate_scripts=gate_scripts,
            hook_installed=True,
            hook_path=hook_path,
            skipped_reason=None,
        )

    def _install_gates(self) -> InjectionResult:
        """Instala os gates no alvo.

        Fonte unica: as pecas do almoxarifado (CATALOGO.json), para o sha256
        instalado conferir com o catalogo na prontidao do C1. O `Injector`
        geral injeta primeiro os templates (conteudo identico as pecas);
        aqui o gate recem-injetado e PROMOVIDO para a peca do catalogo.
        Gate ja na versao certa e pulo (idempotencia); gate editado a mao e
        pulo tambem — a prontidao do C1 acusa a divergencia com dica.
        O template local fica como origem de gates sem peca catalogada.
        """
        source = self.templates_root / GATES_SUBDIR
        if not source.exists():
            raise FileNotFoundError(f"templates de gates nao encontrados: {source}")

        destination = self.target_root / GATES_SUBDIR
        destination.mkdir(parents=True, exist_ok=True)
        pecas_catalogo = _pecas_de_gates_do_almoxarifado()

        result = InjectionResult()
        for template in sorted(source.glob("G_*.py")):
            origem = pecas_catalogo.get(template.name, template)
            alvo = destination / template.name

            if alvo.exists() and not self.force:
                atual = alvo.read_bytes()
                if atual == origem.read_bytes():
                    result.skipped.append(alvo)  # ja esta na versao certa
                    continue
                if atual != template.read_bytes():
                    result.skipped.append(alvo)  # editado a mao; prontidao cobra
                    continue

            sobrescrito = alvo.exists()
            shutil.copy2(origem, alvo)
            _make_executable(alvo)
            (result.overwritten if sobrescrito else result.created).append(alvo)
        return result

    def _provisioned_gate_names(self) -> tuple[str, ...]:
        destination = self.target_root / GATES_SUBDIR
        if not destination.exists():
            return ()
        return tuple(sorted(p.name for p in destination.glob("G_*.py")))


def _resolve_git_dir(target_root: Path) -> Path | None:
    """Resolve o diretorio `.git` real, seguindo o ponteiro `gitdir:` de worktrees."""
    git_path = target_root / ".git"

    if git_path.is_dir():
        return git_path

    if git_path.is_file():
        content = git_path.read_text(encoding="utf-8").strip()
        if content.startswith("gitdir:"):
            raw = content.split(":", 1)[1].strip()
            gitdir = Path(raw)
            resolved = gitdir if gitdir.is_absolute() else (target_root / gitdir)
            return resolved.resolve() if resolved.exists() else None

    return None


def _make_executable(path: Path) -> None:
    """Adiciona o bit de execucao (no-op efetivo no Windows, exigido em POSIX)."""
    current = path.stat().st_mode
    path.chmod(current | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _pecas_de_gates_do_almoxarifado() -> dict[str, Path]:
    """Peca do catalogo de cada gate instalavel: `{G_X.py: caminho_arquivo}`.

    Prioridade da variante `gates/variantes/aidd-forge/G_X.py` (implementacao
    independente do forge, hook-compativel) sobre a principal `gates/G_X.py`
    — mesma regra de resolucao do almoxarifado. `injetor/variantes/aidd-forge/`
    entra por ultimo (e de onde vem o G_INJECT). Dict vazio quando o catalogo
    nao existe (forge standalone): nesse caso a instalacao cai nos templates
    locais e a prontidao do C1 reprova depois, porque sem catalogo nao ha
    hash para conferir.
    """
    from aidd_forge.core.almoxarifado import _encontrar_raiz, carregar_catalogo

    try:
        raiz = _encontrar_raiz()
        catalogo = carregar_catalogo(raiz)
    except (FileNotFoundError, ValueError, OSError):
        return {}

    resolvidas: dict[str, Path] = {}
    prioridades: dict[str, int] = {}
    for peca in catalogo.get("pecas", []):
        nome = str(peca.get("nome", ""))
        caminho = peca.get("caminho")
        if not caminho:
            continue
        eh_gate_principal = nome.startswith("gates/") and "/variantes/" not in nome
        eh_gate_variante_forge = nome.startswith("gates/variantes/aidd-forge/")
        eh_gate_injetor = nome.startswith("injetor/variantes/aidd-forge/G_")
        if not (eh_gate_principal or eh_gate_variante_forge or eh_gate_injetor):
            continue
        arquivo = raiz / caminho
        if not arquivo.is_file():
            continue
        prioridade = 3 if eh_gate_injetor else (2 if eh_gate_variante_forge else 1)
        if prioridade >= prioridades.get(arquivo.name, 0):
            resolvidas[arquivo.name] = arquivo
            prioridades[arquivo.name] = prioridade
    return resolvidas
