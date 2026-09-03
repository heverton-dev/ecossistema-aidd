"""Roteador de Slash Commands e Intent Router em Linguagem Natural.

Mapeia `/forge` e `/aidd-init` para as pastas de comandos das IDEs
suportadas (`.cursor/rules/`, `.claude/commands/`, `.agent/commands/`),
gravando um arquivo de comando por IDE (mecanica pura, custo zero de
tokens). Tambem garante que o `governance/AGENTS.md` do projeto alvo
contenha a secao de Intent Router em Linguagem Natural, injetando-a
quando ausente para projetos com um `AGENTS.md` pre-existente que a
`Injector` preservou (self-healing, idempotente).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

# Pastas de comandos de IDE onde os slash commands sao gravados.
IDE_COMMAND_DIRS: tuple[str, ...] = (".cursor/rules", ".claude/commands", ".agent/commands")

# Comandos mapeados: nome do arquivo -> conteudo markdown do comando.
SLASH_COMMANDS: dict[str, str] = {
    "forge": (
        "# /forge\n\n"
        "Reinjeta/atualiza a infraestrutura AIDD neste projeto.\n\n"
        "Executa: `python -m aidd_forge.cli init`\n"
    ),
    "aidd-init": (
        "# /aidd-init\n\n"
        "Alias de `/forge` para a primeira configuracao do projeto.\n\n"
        "Executa: `python -m aidd_forge.cli init`\n"
    ),
}

AGENTS_MD_RELATIVE = Path("governance") / "AGENTS.md"

INTENT_ROUTER_MARKER = "## Disparo por Linguagem Natural"

INTENT_ROUTER_SECTION = (
    "\n## Disparo por Linguagem Natural\n\n"
    "Se o usuario pedir, em linguagem natural, para \"preparar o ambiente\", "
    "\"configurar este projeto com aidd\" ou \"blindar as regras\", trate como "
    "equivalente a `/forge`.\n\n"
    "Se o usuario pedir, em linguagem natural, para injetar um novo componente, "
    "trate como equivalente a `forge inject <tipo> <nome> --descricao \"...\" "
    "--conteudo \"...\"`:\n"
    "- \"crie uma skill de X\" / \"adicione uma skill para X\" -> `forge inject skill x`\n"
    "- \"crie um mcp de X\" / \"adicione um mcp para X\" -> `forge inject mcp x`\n"
    "- \"crie uma regra sobre X\" / \"nova regra de X\" -> `forge inject rule x`\n"
    "- \"crie uma spec para X\" / \"escreva a spec de X\" -> `forge inject spec x`\n"
    "- \"crie um roteiro de X\" / \"escreva um tutorial de X\" -> `forge inject roteiro x`\n"
)


@dataclass
class SlashRouterResult:
    """Resumo do roteamento de slash commands e da injecao do Intent Router."""

    created: list[Path] = field(default_factory=list)
    overwritten: list[Path] = field(default_factory=list)
    skipped: list[Path] = field(default_factory=list)
    intent_router_injected: bool = False


class SlashRouter:
    """Grava os slash commands nas pastas de IDE e blinda o Intent Router."""

    def __init__(self, target_root: Path, force: bool = False):
        self.target_root = Path(target_root)
        self.force = force

    def run(self) -> SlashRouterResult:
        """Executa o roteamento completo: comandos de IDE + Intent Router."""
        result = SlashRouterResult()
        self._write_ide_commands(result)
        result.intent_router_injected = self._ensure_intent_router()
        return result

    def _write_ide_commands(self, result: SlashRouterResult) -> None:
        for ide_dir in IDE_COMMAND_DIRS:
            for command, content in SLASH_COMMANDS.items():
                dst = self.target_root / ide_dir / f"{command}.md"
                dst.parent.mkdir(parents=True, exist_ok=True)

                if dst.exists():
                    if not self.force:
                        result.skipped.append(dst)
                        continue
                    result.overwritten.append(dst)
                else:
                    result.created.append(dst)

                dst.write_text(content, encoding="utf-8")

    def _ensure_intent_router(self) -> bool:
        """Injeta a secao de Intent Router no `AGENTS.md` alvo se estiver ausente."""
        agents_path = self.target_root / AGENTS_MD_RELATIVE
        if not agents_path.exists():
            return False

        current = agents_path.read_text(encoding="utf-8")
        if INTENT_ROUTER_MARKER in current:
            return False

        agents_path.write_text(current.rstrip("\n") + "\n" + INTENT_ROUTER_SECTION, encoding="utf-8")
        return True
