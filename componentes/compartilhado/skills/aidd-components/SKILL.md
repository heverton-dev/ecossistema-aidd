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

## Negative Guardrails

- NEVER edit `.claude/skills/`, `.agents/skills/`, `.opencode/skills/` or `.gemini/extensions/`: the next `components sync` overwrites them, and `auto_ingest_skills()` turns a stray harness-only folder into a new canonical skill.
- NEVER run `components sync` without `--tipo` (`G_SYNC_CMD_ROT` fails the bare form in live docs).
- NEVER delete a renamed or removed component's harness copies without the user's OK listing each path; sync only prunes leftover files inside a component folder (`_remover_sobras_diretorio`), never whole folders.
- NEVER copy a third-party skill registered in `gates/dependencias_externas.json` into `componentes/`; its vendor installer owns it (`aidd-dependencies`).
- NEVER declare done on sync output alone, nor commit with `--no-verify`: only `components verify` exit 0 proves the copies match the source hash.

## Failure Modes & Fallback

- **verify reports drift or orphan:** rerun `python ecossistema.py components sync --tipo <type>`; if the orphan is a whole old folder, list it to the user and remove it only after approval, then verify again.
- **Unexpected `[AUTO-INGEST]` line in sync output:** a skill existed only in a harness folder. Diff it against the intended source, keep one canonical copy in `componentes/compartilhado/skills/<name>/`, and tell the user.
- **`G_COMPONENTE_AGNOSTICO` fails at pre-commit:** a touched component lacks a harness copy listed in `gates/manifesto_harnesses.json`; resync that `--tipo` instead of copying files by hand.

## Stopping Checklist

- [ ] Only `componentes/<scope>/...` files changed by hand: `git status --porcelain -- componentes/` lists them and every harness diff comes from sync.
- [ ] `python ecossistema.py components sync --tipo <type> > sync.txt 2>&1; echo $? > sync.rc` holds `0`.
- [ ] `python ecossistema.py components verify --tipo <type> > verify.txt 2>&1; echo $? > verify.rc` holds `0`.
- [ ] `python gates/G_SKILL_ROT.py > rot.txt 2>&1; echo $? > rot.rc` holds `0` (no orphan after a rename or delete).
