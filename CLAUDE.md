# Claude Agent Pointer
Canonical governance and instructions: [AGENTS.md](AGENTS.md)

## Mandatory Answer Shape (Rule 10 / Law #4)
Enforced in this harness via `.claude/hooks/regra10_check.py`:
1. One top sentence stating what to do or what happened. No preamble.
2. Short bulleted body. Facts, numbers, findings. No narration of steps taken.
3. One closing suggestion block, separated from the body.
Forbidden: introductions, restating the request, recapping what was just said, listing options without a recommendation.
