"""Flight Plan generator for the ORCA multi-agent orchestrator.

Reads a parsed plan and a harness profile, then compiles a deterministic
flight plan (one row per Front) with branch, worktree, and command.
Zero LLM cost — pure mechanical transformation.
"""

from __future__ import annotations

from pathlib import Path

try:
    from plan_parser import parse_plan
    from agent_spawner import carregar_perfil, compilar_comando
except ImportError:
    from scripts.plan_parser import parse_plan
    from scripts.agent_spawner import carregar_perfil, compilar_comando


COMMAND_TRUNCATE_LEN = 80


def gerar_plano_de_voo(
    plan_dir: str | Path,
    profiles_path: str | Path,
    harness: str = "mimo",
    harness_map: dict[str, str] | None = None,
    interactive: bool = False,
) -> dict:
    """Generate a flight plan from a plan folder and a harness profile.

    Args:
        plan_dir: Path to the plan directory.
        profiles_path: Path to the harness_profiles.json file.
        harness: Default harness profile to use.
        harness_map: Optional dict mapping front name to specific harness profile.
        interactive: If True, compiles command for interactive execution.

    Returns:
        Dict with keys: plan_dir, harness, profile_binary, fronts (list of dicts).
        Each front dict: name, branch, worktree, harness, command (list[str]).
    """
    plan = parse_plan(plan_dir)
    default_profile = carregar_perfil(profiles_path, harness)

    compiled_fronts = []
    for front in plan.fronts:
        front_harness = (harness_map or {}).get(front.name, harness)
        profile = carregar_perfil(profiles_path, front_harness) if front_harness != harness else default_profile
        command = compilar_comando(profile, front.prompt, interactive=interactive)
        rotulo = plan.rotulo(front)
        branch = f"orca/{rotulo}"
        worktree = rotulo
        compiled_fronts.append({
            "name": front.name,
            "rotulo": rotulo,
            "branch": branch,
            "worktree": worktree,
            "harness": front_harness,
            "command": command,
        })

    return {
        "plan_dir": str(plan.folder),
        "harness": harness,
        "profile_binary": default_profile["binary"],
        "fronts": compiled_fronts,
        "interactive": interactive,
    }


def renderizar_plano_de_voo(data: dict) -> str:
    """Render a human-readable markdown table from a flight plan dict.

    Returns a string with a header block and one row per front.
    Long commands are truncated for readability.
    """
    lines: list[str] = []
    harness_label = data["harness"] if not any(f.get("harness") != data["harness"] for f in data["fronts"]) else "Multi-Harness"
    lines.append(f"# Flight Plan — {harness_label}")
    lines.append(f"Plan dir: `{data['plan_dir']}`")
    lines.append(f"Fronts: {len(data['fronts'])}")
    if data.get("interactive"):
        lines.append("Mode: `Interactive Worktrees (User Session)`")
    lines.append("")
    lines.append("| # | Front | Branch | Worktree | Harness | Command (truncated) |")
    lines.append("|---|-------|--------|----------|---------|---------------------|")

    for i, f in enumerate(data["fronts"], 1):
        cmd_str = " ".join(f["command"])
        if len(cmd_str) > COMMAND_TRUNCATE_LEN:
            cmd_str = cmd_str[: COMMAND_TRUNCATE_LEN - 3] + "..."
        lines.append(
            f"| {i} | {f['name']} | `{f['branch']}` | `{f['worktree']}` | {f.get('harness', data.get('harness', '-'))} | `{cmd_str}` |"
        )

    lines.append("")
    return "\n".join(lines)
