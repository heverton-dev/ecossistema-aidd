"""Real ORCA app flight plan compiler.

Unlike flight_plan.py (our own native git-worktree engine) and
subagent_plan.py (Agent tool of the current session), this module compiles a
plan for a THIRD execution environment: the real Orca desktop application,
driven through the `orca` CLI (worktree/terminal/repo commands) -- see
D:/PAPERS/MANUAL_ORCA_ORCHESTRATOR.md and D:/PAPERS/ORCA-GUIA-ORQUESTRACAO.md.

The real Orca app separates "launch the harness" from "send the task text"
into two distinct commands (`orca terminal create` then `orca terminal
send`), and needs a live repoId + terminal handle that only exist once the
agent actually calls those commands -- this module can only pre-compute the
static parts (front name, branch, bare launch command, prompt text). The
live orca-cli calls themselves are made by the assistant session, following
the `orchestrate` skill protocol -- this compiler never executes anything
(same zero-LLM/zero-tool-access boundary as flight_plan.py and
subagent_plan.py).

Mesa Filha, nunca Mesa Solta: every worktree created for a front MUST use
--parent-worktree (default "active"), never --no-parent, so it appears
nested under the project in the ORCA app sidebar instead of loose at the
root (explicit user rule, matches ORCA-GUIA-ORQUESTRACAO.md section 2).
"""

from __future__ import annotations

import subprocess
from pathlib import Path

try:
    from plan_parser import parse_plan
    from agent_spawner import carregar_perfil, compilar_comando_bare
except ImportError:
    from scripts.plan_parser import parse_plan
    from scripts.agent_spawner import carregar_perfil, compilar_comando_bare


PARENT_WORKTREE_PADRAO = "active"


def _branch_atual(repo_path: Path) -> str:
    """Real current git branch of the repo -- never fabricated. Falls back to
    'main' only if the git command itself fails (e.g. detached HEAD), which
    is a reported fallback, not a silently guessed fact."""
    try:
        resultado = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=repo_path, capture_output=True, text=True, check=True,
        )
        branch = resultado.stdout.strip()
        return branch if branch and branch != "HEAD" else "main"
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "main"


def compilar_plano_orca(
    plan_dir: str | Path,
    profiles_path: str | Path,
    repo_path: str | Path,
    harness: str = "claude",
    harness_map: dict[str, str] | None = None,
    parent_worktree: str = PARENT_WORKTREE_PADRAO,
) -> dict:
    """Compile a plan folder into a real-ORCA-app flight plan.

    Returns dict: plan_dir, mode, repo_path, parent_worktree, base_branch,
    fronts (list of dicts: name, branch, harness, launch_command (list[str],
    NEVER includes the prompt), prompt (str, sent separately via
    `orca terminal send` once the terminal is running)).
    """
    plan = parse_plan(plan_dir)
    repo_path = Path(repo_path).resolve()
    default_profile = carregar_perfil(profiles_path, harness)
    base_branch = _branch_atual(repo_path)

    fronts = []
    for front in plan.fronts:
        front_harness = (harness_map or {}).get(front.name, harness)
        profile = (
            carregar_perfil(profiles_path, front_harness)
            if front_harness != harness else default_profile
        )
        rotulo = plan.rotulo(front)
        fronts.append({
            "name": front.name,
            "rotulo": rotulo,
            "worktree_name": rotulo,
            "branch": f"orca/{rotulo}",
            "harness": front_harness,
            "launch_command": compilar_comando_bare(profile),
            "prompt": front.prompt,
        })

    return {
        "plan_dir": str(plan.folder),
        "mode": "orca",
        "repo_path": str(repo_path),
        "parent_worktree": parent_worktree,
        "base_branch": base_branch,
        "fronts": fronts,
    }


def renderizar_plano_orca(data: dict) -> str:
    """Human-readable markdown preview of an Orca-app flight plan."""
    lines: list[str] = []
    lines.append("# Flight Plan — ORCA (aplicativo real)")
    lines.append(f"Repo: `{data['repo_path']}`")
    lines.append(f"Plan dir: `{data['plan_dir']}`")
    lines.append(f"Base branch: `{data['base_branch']}`")
    lines.append(f"Parent worktree: `{data['parent_worktree']}` (mesa sempre filha, nunca solta)")
    lines.append(f"Fronts: {len(data['fronts'])}")
    lines.append("")
    lines.append("| # | Front | Branch | Harness | Launch Command | Prompt (truncado) |")
    lines.append("|---|-------|--------|---------|-----------------|--------------------|")
    for i, f in enumerate(data["fronts"], 1):
        cmd_str = " ".join(f["launch_command"])
        prompt = f["prompt"].replace("\n", " ").strip()
        if len(prompt) > 80:
            prompt = prompt[:77] + "..."
        lines.append(
            f"| {i} | {f['name']} | `{f['branch']}` | {f['harness']} | `{cmd_str}` | `{prompt}` |"
        )
    lines.append("")
    lines.append(
        "⚠️ Nenhuma worktree/terminal real foi criado — isto é só o Plano de Voo "
        "compilado (mecânico, zero-LLM). O assistente da sessão executa cada "
        "frente via `orca-cli` (worktree create --parent-worktree "
        f"{data['parent_worktree']} → terminal create → terminal send), "
        "seguindo o protocolo em componentes/compartilhado/skills/orchestrate/SKILL.md."
    )
    return "\n".join(lines)
