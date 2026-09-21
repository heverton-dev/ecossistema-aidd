# OpenCode Agent Pointer
Canonical governance and instructions: [AGENTS.md](../../AGENTS.md)

## Universal & Agnostic Flow Activation (Law #6)
- The 3 Canonical Creation Flows and Tools are available via slash commands or direct CLI:
  - `/pure [nome] [dominio]` -> Dispara o Fluxo 01 (`aidd-pure` / skill `pure` / `python ecossistema.py pure <args>`)
  - `/open [nome] [dominio]` -> Dispara o Fluxo 02 (`aidd-open` / skill `open` / `python ecossistema.py open <args>`)
  - `/freedom <export> [nome]` -> Dispara o Fluxo 03 (`aidd-freedom` / skill `freedom` / `python ecossistema.py freedom <args>`)
  - `/bridge <subcomando> <args>` -> Executa operacoes atomicas de `aidd-bridge` (skill `bridge` / `python ecossistema.py bridge <args>`)
- All skills are located in `.opencode/skills/` and commands in `.opencode/commands/`.
- When any of these commands or natural language equivalents are received, execute the corresponding skill or CLI command immediately.

## Mandatory Answer Shape (Rule 10 / Law #4)
1. One top sentence stating what to do or what happened. No preamble.
2. Short bulleted body. Facts, numbers, findings. No narration of steps taken.
3. One closing suggestion block, separated from the body.
Forbidden: introductions, restating the request, recapping what was just said, listing options without a recommendation. Target tokens: ≤300. Language: PT-BR.
