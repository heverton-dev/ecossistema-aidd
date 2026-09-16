"""Roteador de Slash Commands e Intent Router em Linguagem Natural.

Mapeia `/forge` e `/aidd-init` para as pastas de comando dos harnesses
suportados, gravando um arquivo de comando por harness (mecanica pura,
custo zero de tokens). Tambem garante que o `governance/AGENTS.md` do
projeto alvo contenha a secao de Intent Router em Linguagem Natural,
injetando-a quando ausente para projetos com um `AGENTS.md` pre-existente
que a `Injector` preservou (self-healing, idempotente).

As pastas de destino vem de `gates/manifesto_harnesses.json` (fonte unica
de harnesses do ecossistema, ja usada por `scripts/gestor_componentes.py`
e `gates/G_HARNESS_COMPAT.py`) via `aidd_forge.core.harness_manifest` —
nunca de uma lista propria hardcoded aqui. Achado real (2026-09-15): a lista
antiga (`.cursor/rules`, `.claude/commands`, `.agent/commands`) estava
dessincronizada desse manifesto ha tempo: o caminho confirmado do Cursor e
`.cursor/commands` (nao `.cursor/rules`), e `.agent/commands` nunca foi o
endereco oficial de nenhum harness — faltavam Antigravity (`.agents`),
OpenCode (`.opencode`), MimoCode (`.mimocode`) e CodeBuddy (`.codebuddy`)
por completo. Ler do manifesto (num modulo compartilhado, tambem usado por
`forge inject command`) evita que os consumidores voltem a divergir entre si.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from aidd_forge.core.harness_manifest import carregar_command_dirs_canonicos

# Pastas de comando dos harnesses suportados, derivadas do manifesto unico.
IDE_COMMAND_DIRS: tuple[str, ...] = carregar_command_dirs_canonicos()

# Conteudo base (usado quando nao ha um `ecossistema.py` do toolbox por perto, ex:
# aidd-forge usado standalone fora do monorepo ecossistema-aidd).
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


def _build_slash_commands(
    target_root: Path, ecossistema_script: Path | None
) -> dict[str, str]:
    """Monta o conteudo dos comandos, auto-contido quando o toolbox e encontrado.

    Sem `ecossistema_script`, cai no conteudo base (`python -m aidd_forge.cli init`),
    que exige o pacote `aidd-forge` corretamente instalado no Python do ambiente.
    Com `ecossistema_script`, o comando real gravado ja embute o caminho absoluto do
    toolbox e do projeto alvo — nao depende de nenhum registro pip (`pip -e`) que possa
    ficar orfao se o clone do toolbox for movido, renomeado ou apagado.
    """
    if ecossistema_script is None:
        return dict(SLASH_COMMANDS)

    comando_real = (
        f'python "{ecossistema_script}" forge init "{target_root}"'
    )
    return {
        "forge": (
            "# /forge\n\n"
            "Reinjeta/atualiza a infraestrutura AIDD neste projeto.\n\n"
            "Comando real (auto-contido, nao depende de instalacao pip):\n\n"
            f"```bash\n{comando_real}\n```\n\n"
            "(equivalente interno, caso rode a ferramenta isolada com o pacote "
            "`aidd-forge` instalado no ambiente: `python -m aidd_forge.cli init`)\n"
        ),
        "aidd-init": (
            "# /aidd-init\n\n"
            "Alias de `/forge` para a primeira configuracao do projeto.\n\n"
            "Comando real (auto-contido, nao depende de instalacao pip):\n\n"
            f"```bash\n{comando_real}\n```\n\n"
            "(equivalente interno, caso rode a ferramenta isolada com o pacote "
            "`aidd-forge` instalado no ambiente: `python -m aidd_forge.cli init`)\n"
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

    def __init__(
        self,
        target_root: Path,
        force: bool = False,
        ecossistema_script: Path | None = None,
        command_dirs: tuple[str, ...] | None = None,
    ):
        self.target_root = Path(target_root)
        self.force = force
        self.ecossistema_script = (
            Path(ecossistema_script) if ecossistema_script is not None else None
        )
        self.command_dirs = command_dirs if command_dirs is not None else IDE_COMMAND_DIRS

    def run(self) -> SlashRouterResult:
        """Executa o roteamento completo: comandos de IDE + Intent Router."""
        result = SlashRouterResult()
        self._write_ide_commands(result)
        result.intent_router_injected = self._ensure_intent_router()
        return result

    def _write_ide_commands(self, result: SlashRouterResult) -> None:
        commands = _build_slash_commands(self.target_root, self.ecossistema_script)
        for ide_dir in self.command_dirs:
            for command, content in commands.items():
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
