---
name: aidd-components
description: Creates or updates agnostic ecosystem components (skills, commands, hooks, mcps, specs, configs, sub-agents, scripts) in the single source componentes/ and distributes them to every harness with components sync and verify. Use when the user asks to create, update or sync a component, or says "componente", "sincronizar componentes", "components sync", "distribuir para os harnesses".
---

# aidd-components

## Protocol

1. **Write only in the single source** `componentes/<tool or compartilhado>/<type>/<name>/...`, following the unit and folder convention of `gates/manifesto_harnesses.json`:
   - `skill`: `componentes/<scope>/skills/<name>/SKILL.md`
   - `mcp`: `componentes/<scope>/mcps/<name>/server.py`
   - `spec`: `componentes/<scope>/specs/<name>.md`
   - `config`: `componentes/<scope>/config/<name>.json`
   - `command`: `componentes/<scope>/comandos/<name>.md`
   - `hook`: `componentes/<scope>/hooks/<name>/...`
   - `sub-agent`: `componentes/<scope>/subagentes/<name>.md`
   - `script`: `componentes/<scope>/scripts/<name>.py`

   Harness folders (`.claude/`, `.agents/`, `.opencode/`, `.gemini/`...) are generated destinations: never edit them.
2. **Distribute** (zero sync logic in the agent):
   ```bash
   python ecossistema.py components sync --tipo <type> [--ferramenta <name>]
   ```
3. **Verify:**
   ```bash
   python ecossistema.py components verify --tipo <type|todos> [--ferramenta <name>]
   ```
   Done when verify exits 0.
4. **Report facts:** show the command output itself, naming which harness folders received the component.

Renaming or deleting a skill: sync never deletes, so remove the old folder from every harness destination too, or `G_SKILL_ROT` flags it as an orphan.
