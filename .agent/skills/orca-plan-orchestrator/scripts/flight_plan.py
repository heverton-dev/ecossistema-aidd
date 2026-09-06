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
) -> dict:
    """Generate a flight plan from a plan folder and a harness profile.

    Args:
        plan_dir: Path to the plan directory.
        profiles_path: Path to the harness_profiles.json file.
        harness: Name of the harness profile to use.

    Returns:
        Dict with keys: plan_dir, harness, profile, fronts (list of dicts).
        Each front dict: name, branch, worktree, command (list[str]).
    """
    plan = parse_plan(plan_dir)
    profile = carregar_perfil(profiles_path, harness)

    compiled_fronts = []
    for front in plan.fronts:
        command = compilar_comando(profile, front.content)
        branch = f"orca/{front.name}"
        worktree = f"wt-{front.name}"
        compiled_fronts.append({
            "name": front.name,
            "branch": branch,
            "worktree": worktree,
            "command": command,
        })

    return {
        "plan_dir": str(plan.folder),
        "harness": harness,
        "profile_binary": profile["binary"],
        "fronts": compiled_fronts,
    }


def renderizar_plano_de_voo(data: dict) -> str:
    """Render a human-readable markdown table from a flight plan dict.

    Returns a string with a header block and one row per front.
    Long commands are truncated for readability.
    """
    lines: list[str] = []
    lines.append(f"# Flight Plan — {data['harness']}")
    lines.append(f"Plan dir: `{data['plan_dir']}`")
    lines.append(f"Binary: `{data['profile_binary']}`")
    lines.append(f"Fronts: {len(data['fronts'])}")
    lines.append("")
    lines.append("| # | Front | Branch | Worktree | Command (truncated) |")
    lines.append("|---|-------|--------|----------|---------------------|")

    for i, f in enumerate(data["fronts"], 1):
        cmd_str = " ".join(f["command"])
        if len(cmd_str) > COMMAND_TRUNCATE_LEN:
            cmd_str = cmd_str[: COMMAND_TRUNCATE_LEN - 3] + "..."
        lines.append(
            f"| {i} | {f['name']} | `{f['branch']}` | `{f['worktree']}` | `{cmd_str}` |"
        )

    lines.append("")
    return "\n".join(lines)
