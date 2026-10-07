---
name: aidd-forge
description: Bootstraps and hardens a target repository with the aidd-forge governance kit (quality gates, git hooks, token-economy rules, phase isolation). Use when the user asks to bootstrap, initialize or harden a project, or says "forge", "/forge", "blindar projeto", "inicializar governança".
---

# aidd-forge

Injects the full AI-Driven Development kit into a target repository:
- ephemeral subagent orchestration with context purge;
- deterministic quality gates and git hooks;
- extreme token-economy rules (Caveman Ultra);
- phase slicing with isolated micro-environments.

## Run

```bash
python ecossistema.py forge init [path]
```

Slash command: `/forge [path]`. Without a path it uses the current directory.

Done when: the command exits 0 and the target contains the injected gates and hooks.

## Negative Guardrails

- NEVER run `python ecossistema.py forge init` without an explicit `[path]` from the ecosystem root: the default target is the current directory, so the kit lands in the ecosystem itself.
- NEVER add `--force` on a target the user already customized without listing the files it overwrites and getting an explicit OK (`run-fluxo` already calls `forge init <pasta> --force` on fresh folders only).
- NEVER hand-edit `handoff-forge.json`. After any change to `scripts/*.py` or `modulos/01-governanca-e-qualidade/gates/G_aidd_forge.py`, re-emit it with `python ecossistema.py forge handoff emit` (the Mobbin change left it stale once; fixed in 4db900a).
- NEVER delete orphan files or `.FORGE-ROLLBACK-JOURNAL.json` by hand after a crash; run `python componentes/compartilhado/skills/aidd-forge/scripts/rollback.py <path>`.
- NEVER commit the hardened target with `--no-verify` to get past the hooks forge just installed; fix what the hook reports.
- NEVER prove the fix with `python -m aidd_forge.cli`: `ecossistema.py forge` runs `.agents/skills/aidd-forge/scripts/cli.py` first, so test through `python ecossistema.py forge`.

## Failure Modes & Fallback

- **Crash mid-init (half-written target):** run `python componentes/compartilhado/skills/aidd-forge/scripts/rollback.py <path>`; "nada a recuperar" or "rollback recuperou N" with exit 0 means clean, then rerun `forge init <path>`.
- **`forge handoff verify` exits 1 ("hash divergente"):** a forge script changed after the last emit. If you changed it, run `forge handoff emit` and verify again; if you did not, stop and ask the user who changed it.
- **`python modulos/01-governanca-e-qualidade/gates/G_aidd_forge.py --alvo <path>` fails:** run `python ecossistema.py forge audit <path>`, then `forge conform <path> --dry-run`; apply `forge conform <path>` only after the user sees the dry-run list.
- **"nao foi possivel auto-reparar a instalacao pip -e":** only the pip fallback broke; the skill-local `cli.py` route still works. Report it, do not `pip install` into another clone.

## Stopping Checklist

- [ ] `python ecossistema.py forge init <path> > forge.log 2>&1; echo $? > forge.rc` and `forge.rc` holds `0`.
- [ ] `python modulos/01-governanca-e-qualidade/gates/G_aidd_forge.py --alvo <path> > gforge.log 2>&1; echo $? > gforge.rc` and `gforge.rc` holds `0`.
- [ ] If forge scripts changed: `python ecossistema.py forge handoff verify > hverify.log 2>&1; echo $? > hverify.rc` holds `0`.
- [ ] `<path>/.FORGE-ROLLBACK-JOURNAL.json` does not exist (no pending transaction).
- [ ] `git -C <path> status --short` lists only files forge reported as injected.
