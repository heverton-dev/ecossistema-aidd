"""Tests for agent_spawner command compiler.

Verifies that compilar_comando produces the exact argument list
for all 4 harness profiles, using the corrected values from
real --help inspection (2026-09-06).
"""

import json
from pathlib import Path

import pytest

from scripts.agent_spawner import carregar_perfil, compilar_comando

PROFILES_PATH = Path(__file__).resolve().parent.parent / ".orca" / "harness_profiles.json.example"
SAMPLE_PROMPT = "Explique o design do modulo X"


@pytest.fixture
def profiles():
    return json.loads(PROFILES_PATH.read_text(encoding="utf-8"))["profiles"]


# ---------------------------------------------------------------------------
# mimo: --yolo --pure --model <model> --prompt <text>
# ---------------------------------------------------------------------------
def test_mimo_compiled_args(profiles):
    args = compilar_comando(profiles["mimo"], SAMPLE_PROMPT)
    expected = [
        "mimo",
        "--yolo",
        "--pure",
        "--model", "mimo/mimo-v2.5-pro",
        "--prompt", SAMPLE_PROMPT,
    ]
    assert args == expected


# ---------------------------------------------------------------------------
# opencode: --auto --pure --model <model> --prompt <text>
# ---------------------------------------------------------------------------
def test_opencode_compiled_args(profiles):
    args = compilar_comando(profiles["opencode"], SAMPLE_PROMPT)
    expected = [
        "opencode",
        "--auto",
        "--pure",
        "--model", "opencode/default",
        "--prompt", SAMPLE_PROMPT,
    ]
    assert args == expected


# ---------------------------------------------------------------------------
# claude: --dangerously-skip-permissions -p --model <model> <text>
#         prompt is POSITIONAL (last element), -p is a boolean flag
# ---------------------------------------------------------------------------
def test_claude_compiled_args(profiles):
    args = compilar_comando(profiles["claude"], SAMPLE_PROMPT)
    expected = [
        "claude",
        "--dangerously-skip-permissions",
        "-p",
        "--model", "claude-sonnet-4-20250514",
        SAMPLE_PROMPT,
    ]
    assert args == expected


# ---------------------------------------------------------------------------
# agy: --dangerously-skip-permissions --print --model <model> <text>
#       prompt is POSITIONAL (last element), --print is a boolean flag
#       NOTE: agy prompt mechanism remains OPEN (not confirmed by real invocation)
# ---------------------------------------------------------------------------
def test_agy_compiled_args(profiles):
    args = compilar_comando(profiles["agy"], SAMPLE_PROMPT)
    expected = [
        "agy",
        "--dangerously-skip-permissions",
        "--print",
        SAMPLE_PROMPT,
    ]
    assert args == expected


# ---------------------------------------------------------------------------
# Edge: prompt with spaces and special chars
# ---------------------------------------------------------------------------
def test_prompt_with_special_chars(profiles):
    weird = 'Busca "modulo X" -- e retorna <resultado>'
    args = compilar_comando(profiles["claude"], weird)
    # prompt must be a single list element, not shell-split
    assert args[-1] == weird
    assert len(args) == 6  # binary + auto_approve + -p + model_flag + model_value + prompt


# ---------------------------------------------------------------------------
# Edge: unknown prompt_mode raises ValueError
# ---------------------------------------------------------------------------
def test_unknown_prompt_mode_raises():
    bad_profile = {
        "binary": "fake",
        "auto_approve_flag": "--auto",
        "prompt_mode": "magic",
        "prompt_flag": None,
        "model_flag": "--model",
        "default_model": "x",
        "extra_flags": [],
    }
    with pytest.raises(ValueError, match="prompt_mode desconhecido"):
        compilar_comando(bad_profile, "hello")


# ---------------------------------------------------------------------------
# Edge: flag_value without prompt_flag raises ValueError
# ---------------------------------------------------------------------------
def test_flag_value_missing_prompt_flag_raises():
    bad_profile = {
        "binary": "fake",
        "auto_approve_flag": "--auto",
        "prompt_mode": "flag_value",
        "prompt_flag": None,
        "model_flag": "--model",
        "default_model": "x",
        "extra_flags": [],
    }
    with pytest.raises(ValueError, match="prompt_flag ausente"):
        compilar_comando(bad_profile, "hello")
