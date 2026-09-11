"""Subagent Flight Plan compiler for the ORCA ADE orchestrator.

Alternative to flight_plan.py's worktree/terminal mode: compiles each front
of a plan into a subagent spec (subagent_type, model, prompt) meant to be
executed via the Agent tool of the CURRENT chat session -- never a worktree,
never a separate terminal, shared context (no file isolation).

This module never spawns anything. Same zero-LLM mechanical boundary as
flight_plan.py: a plain script has no model/Agent-tool access, so execution
of the compiled plan is always done by the live assistant session, guided by
the `orchestrate` skill protocol, reading the (possibly user-edited) JSON
this module writes via plan_io.salvar_plano_de_voo.
"""

from __future__ import annotations

from pathlib import Path

try:
    from plan_parser import parse_plan
except ImportError:
    from scripts.plan_parser import parse_plan


DEFAULT_SUBAGENT_TYPE = "general-purpose"

COMMAND_TRUNCATE_LEN = 80


def compilar_plano_subagentes(
    plan_dir: str | Path,
    subagent_type: str = DEFAULT_SUBAGENT_TYPE,
    model: str | None = None,
    subagent_map: dict[str, str] | None = None,
    model_map: dict[str, str] | None = None,
) -> dict:
    """Compile a plan folder into a subagent-mode flight plan.

    Args:
        plan_dir: Path to the plan directory.
        subagent_type: Default subagent type for fronts not in subagent_map.
        model: Default model override for fronts not in model_map (None means
            "use whatever model this session/subagent_type defaults to").
        subagent_map: Optional dict mapping front name to a specific subagent_type.
        model_map: Optional dict mapping front name to a specific model.

    Returns:
        Dict with keys: plan_dir, mode ("subagent"), fronts (list of dicts).
        Each front dict: name, subagent_type, model, prompt.
    """
    plan = parse_plan(plan_dir)

    fronts = []
    for front in plan.fronts:
        fronts.append({
            "name": front.name,
            "rotulo": plan.rotulo(front),
            "subagent_type": (subagent_map or {}).get(front.name, subagent_type),
            "model": (model_map or {}).get(front.name, model),
            "prompt": front.prompt,
        })

    return {
        "plan_dir": str(plan.folder),
        "mode": "subagent",
        "fronts": fronts,
    }


def renderizar_plano_subagentes(data: dict) -> str:
    """Render a human-readable markdown table for a subagent-mode flight plan."""
    lines: list[str] = []
    lines.append("# Flight Plan — Subagentes (Agent tool desta sessão)")
    lines.append(f"Plan dir: `{data['plan_dir']}`")
    lines.append(f"Fronts: {len(data['fronts'])}")
    lines.append("Mode: `Subagents (shared context — no file isolation)`")
    lines.append("")
    lines.append("| # | Front | Subagent Type | Modelo | Prompt (truncado) |")
    lines.append("|---|-------|---------------|--------|--------------------|")

    for i, f in enumerate(data["fronts"], 1):
        prompt = f["prompt"].replace("\n", " ").strip()
        if len(prompt) > COMMAND_TRUNCATE_LEN:
            prompt = prompt[: COMMAND_TRUNCATE_LEN - 3] + "..."
        modelo = f.get("model") or "(default da sessão)"
        lines.append(f"| {i} | {f['name']} | {f['subagent_type']} | {modelo} | `{prompt}` |")

    lines.append("")
    lines.append(
        "⚠️ Nenhum subagente foi disparado — isto é só o Plano de Voo compilado "
        "(mecânico, zero-LLM). Revise/edite o JSON salvo antes de confirmar a execução."
    )
    return "\n".join(lines)
