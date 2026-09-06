"""Harness command compiler for the ORCA multi-agent orchestrator.

Assembles subprocess argument lists from declarative harness profiles.
Never calls subprocess.run itself -- only builds and returns list[str].
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def carregar_perfil(profiles_path: str | Path, nome: str) -> dict[str, Any]:
    """Load a single harness profile by name from a JSON file."""
    data = json.loads(Path(profiles_path).read_text(encoding="utf-8"))
    if nome not in data["profiles"]:
        raise KeyError(f"Perfil '{nome}' nao encontrado. Disponiveis: {list(data['profiles'])}")
    return data["profiles"][nome]


def compilar_comando(profile: dict[str, Any], sliced_prompt: str) -> list[str]:
    """Compile a harness profile + prompt into a subprocess-ready argument list.

    Returns list[str] -- never a concatenated string.
    Never calls subprocess.run.
    """
    args: list[str] = [profile["binary"]]

    # Auto-approve flag (always present)
    if profile.get("auto_approve_flag"):
        args.append(profile["auto_approve_flag"])

    # Extra static flags (e.g. --pure, -p, --print)
    for flag in profile.get("extra_flags", []):
        args.append(flag)

    # Model flag
    model = profile.get("default_model")
    if model and profile.get("model_flag"):
        args.append(profile["model_flag"])
        args.append(model)

    # Prompt -- the critical difference between harnesses
    prompt_mode = profile.get("prompt_mode", "flag_value")

    if prompt_mode == "flag_value":
        # e.g. mimo/opencode: --prompt <text>
        prompt_flag = profile.get("prompt_flag")
        if not prompt_flag:
            raise ValueError(f"prompt_mode='flag_value' mas prompt_flag ausente no perfil")
        args.append(prompt_flag)
        args.append(sliced_prompt)
    elif prompt_mode == "positional":
        # e.g. claude/agy: prompt is a positional arg at the END
        args.append(sliced_prompt)
    else:
        raise ValueError(f"prompt_mode desconhecido: {prompt_mode}")

    return args
