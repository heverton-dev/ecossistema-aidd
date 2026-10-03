---
name: aidd-orca
description: Native git-worktree engine that executes multi-phase plans (00-PROCESSO-E-DECISOES.md + NN-*.md) with ephemeral worktrees, per-front harness choice, local gate audit before merge and an anti-loop circuit breaker. Called by aidd-orchestrate when the user picks the native git worktree environment. Use when that environment was chosen, or the user says "worktree nativo", "motor de worktree", "orca nativo".
---

# aidd-orca (native git worktree engine)

No slash command of its own: `/orchestrate` has a single owner, `aidd-orchestrate`, which calls this skill only for the **native git worktree** environment. It does not take part in the ORCA app or Subagents environments. Two skills answering the same command with opposite rules once caused tables nested inside tables in the ORCA app.

## Capabilities

- Deterministic plan parser for folders with parallel fronts.
- Ephemeral worktree life cycle (`git worktree` + ephemeral branches).
- Reactive hooks (zero polling) and state sync.
- Local gate audit (exit 0) before any merge.
- Anti-loop circuit breaker against hangs, excess time or inactivity.
- Interactive Flight Plan: harness commands, installed-binary detection, interactive selection.

## Protocol

1. **Inspect the plan and existing state.** The folder must hold `00-PROCESSO-E-DECISOES.md` and `NN-*.md`. Read `.orca/.orca_state.json` if present: fronts in `MERGED` are skipped. Show done and pending fronts.
2. **Harness per front (mandatory).** Never assume one global harness. The current session's harness is the **gate auditor** before each merge. For each pending front ask which harness runs it (`claude`, `agy`, `mimo`, `opencode`, `gemini`, `cursor`, `codebuddy`).
3. **Compile and show the Flight Plan** as a table: number, front name, ephemeral branch, worktree, executor harness, command.
4. **Confirm and run sequentially.**
   - No subagents or background tasks in this path: never call `task create`, `task start`, `invoke_subagent` or background jobs.
   - The assistant compiles the Flight Plan, creates the worktree and shows the developer how to run the front in the terminal.
   - One front at a time, driven by the developer in the terminal.

## CLI

```bash
python ecossistema.py orchestrate [plan]                     # asks mode and harness per front
python ecossistema.py orchestrate [plan] --interactive
python ecossistema.py orchestrate [plan] --interactive --harness-map frente1=claude,frente2=agy
python ecossistema.py orchestrate [plan] --dry-run           # Flight Plan only, zero LLM
```

## Negative Guardrails

- NEVER delete `.orca/.orca_state.json` to get past `[ERRO] ... ja existe`: use `--resume` (fronts in `MERGED` are skipped); clearing `.orca/` needs the user's OK.
- NEVER let the gate auditor be the front's own harness: the current session audits; `gate_auditor.audit_front` runs `python ecossistema.py audit` when a front touches `gates/` or `scripts/`, plus the touched tools' pytest.
- NEVER merge a front that is not `GATE_PASSED` in `.orca/.orca_state.json`, and never with `--no-verify`.
- NEVER raise `CircuitBreakerConfig` limits (`max_execution_time_seconds` 1800, `idle_heartbeat_seconds` 300) to make a hung front pass.
- NEVER use `task create`, `invoke_subagent` or background jobs here, nor answer for the user at `_confirm` (it returns 2 when declined).

## Failure Modes & Fallback

- **`[ERRO] --resume pedido mas .orca/.orca_state.json nao existe`:** first run; rerun without `--resume`.
- **Circuit breaker kills a front (total or idle timeout):** state goes `FAILED`; read `.orca/memory.md` and the front report, tell the user, rerun with `--resume` (FAILED -> retry).
- **Front in `RUNNING` after a crash:** `classify_resume` only flags `resume_running`; check `git -C <worktree> status` and ask the user whether to continue or restart that front.
- **Harness binary missing on the Flight Plan:** pick another installed harness with the user and pass `--harness-map <front>=<harness>`.

## Stopping Checklist

Prove each item with the exit code read from a file (`> x.log 2>&1; echo $? > x.rc`, read `x.rc`), never through a pipe.

- [ ] `python ecossistema.py orchestrate <plan> --dry-run` exit 0 with one harness per pending front.
- [ ] `.orca/.orca_state.json` lists every front as `MERGED`.
- [ ] `python -m pytest componentes/compartilhado/skills/aidd-orca/tests -q` exit 0 when the engine was changed.
- [ ] `git worktree list` shows no ephemeral worktree of this plan.

## Files

- `scripts/`: engine (`orchestrator_engine.py`, `plan_parser.py`, `flight_plan.py`, `orca_real_plan.py`, `subagent_plan.py`, `worktree_engine.py`, `gate_auditor.py`, `circuit_breaker.py`, `state_engine.py`, `hooks.py`, `agent_spawner.py`, `plan_io.py`).
- `tests/`: unit and e2e tests of the engine.
- `.orca/harness_profiles.json.example`: harness profile template.
