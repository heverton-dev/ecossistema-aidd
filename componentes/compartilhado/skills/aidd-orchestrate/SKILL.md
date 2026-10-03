---
name: aidd-orchestrate
description: Routes the execution of an approved plan to one of three environments (ORCA app via orca-cli, subagents of this session, or native git worktrees), compiles the per-environment Flight Plan and runs it only after explicit approval. Step 3 of the melhoria -> plan -> orchestrate flow. Use when the user wants to execute an approved plan, or types "/orchestrate", "orchestrate", "executar plano", "orquestrar plano", "plano de voo".
---

# aidd-orchestrate (step 3 of 3)

Flow: `/melhoria` -> `/plan` -> **`/orchestrate`**. No step triggers the next one by itself (Golden Rule #7, `AGENTS.md`). One owner per command; the native worktree engine lives in `aidd-orca` and has no command of its own.

## One Flight Plan format per environment

| Environment | What really runs | Flight Plan compiler |
|---|---|---|
| **ORCA** | the real ORCA app through `orca-cli` | `orca_real_plan.compilar_plano_orca` (launch command without prompt; task text sent later) |
| **Subagents** | Agent tool of this session (shared context, no worktree) | `subagent_plan.compilar_plano_subagentes` (`subagent_type`/`model`/`prompt` per front) |
| **Native git worktree** | this repo's engine (`orchestrator_engine.py`), plain `git worktree` + harness spawned directly | `flight_plan.gerar_plano_de_voo` (full command ready for `subprocess.run`) |

Never mix formats: that bug produced unexecutable plans in the ORCA app.

## Table name: `PLAN-<NNNN>-fase-<NN>-<short-name>`

Example: `PLAN-0016-fase-04-eliminar-timesleep-injetar`, branch `orca/<same>`. Two-digit phase always (sort order); short name cut to 3 words. Never invent it: use the exact `rotulo` field of each front in `.orca-flight-plan.json` (from `plan_parser.rotulo_da_frente`), including in `--name`.

## Protocol

1. **Environment gate (always the first question):** ask, never assume.
   - **ORCA:** real worktree and terminal in the installed app. Each front is an independent table (`--no-parent`, no `--base-branch`). Child tables (`--parent-worktree`) only when the user asks for stacked work.
   - **Subagents:** no file isolation. Warn the user if fronts touch the same files.
   - **Native git worktree:** real isolation without the ORCA app.
2. **Compile the Flight Plan** (mechanical, zero LLM; never pick harness, model or subagent type without asking):
   ```bash
   python ecossistema.py orchestrate <plan> --ambiente orca --dry-run [--repo-path <path>] [--parent-worktree <selector>]
   python ecossistema.py orchestrate <plan> --ambiente subagent --dry-run [--subagent-type <type>] [--model <model>]
   python ecossistema.py orchestrate <plan> --ambiente gitworktree --dry-run
   ```
   The CLI executes nothing here. Done when `<plan-folder>/.orca-flight-plan.json` exists.
3. **Show the Flight Plan** and the JSON path; invite the user to edit harness, model, subagent_type, prompt, parent-worktree.
4. **Ask for explicit approval** of the (edited or not) Flight Plan. Never fabricate it.
5. **Execute.** The plan becomes IN EXECUTION (and moves to `docs/planos/fazendo/`) only when real execution starts, never on dry-run. Native worktree does it inside the command; for Subagents and ORCA run first:
   ```bash
   python ecossistema.py plan iniciar-execucao <plan-path>
   ```
   - **Native git worktree:** `python ecossistema.py orchestrate <plan> --ambiente gitworktree --harness ... --yes [--resume]`. No subagents or background tasks in this path (rules in `aidd-orca`); only watch the terminal the engine opens.
   - **Subagents:** reread `.orca-flight-plan.json` and, front by front, call the Agent tool with the exact `subagent_type`/`model`/`prompt`. If a front fails or reports a block, stop and tell the user before the next one.
   - **ORCA app:** follow `references/orca-app.md` step by step.

## Do not use when

- The native worktree engine is already running -> `aidd-orca`.
- Generating the plan structure -> `aidd-plan`.
- Operating the ORCA app outside a plan -> the global `orca-cli` skill.

## Negative Guardrails

- NEVER pass `--ambiente`, `--harness` or `--yes` the user did not choose: with no `--ambiente` and no TTY (or with `--yes`/`--dry-run`) `orchestrate_cli` silently falls back to `gitworktree`.
- NEVER run the `worktree create` line from `.orca-flight-plan.json` as is: `orca_real_plan.compilar_plano_orca` emits `--parent-worktree active` (child table), while step 1 requires `--no-parent` unless the user asked for stacked work.
- NEVER call `python ecossistema.py plan iniciar-execucao <plan>` on a dry-run: it moves the plan to `docs/planos/fazendo/` and marks it IN EXECUTION.
- NEVER use `--dangerously-force-headless` or launch a table harness with `--resume <session-id>`: unattended tables once committed and pushed 3 times skipping the gate.
- NEVER run `orca orchestration check` by hand while a 4F phase runs: the re-delivered heartbeat marked the phase "failed — alive".
- NEVER integrate a table on the AI's word or with `--no-verify`: run `python ecossistema.py audit` inside the table, read `git diff`, then cherry-pick.

## Failure Modes & Fallback

- **`terminal wait --for tui-idle` returns `satisfied: false` twice:** report the front as not started, send nothing, close the table terminal (`references/orca-app.md` step 4).
- **Ambiguous `terminal send` receipt:** repeat the SAME command with `--retry-request <id>`; no empty resend.
- **A Subagents front fails or reports a block:** stop before the next front and show the user the front's `rotulo` and error.
- **Hand-edited Flight Plan:** rerun with `--from-flight-plan <plan-folder>/.orca-flight-plan.json` so the edit is not recompiled away.

## Stopping Checklist

Prove each item with the exit code read from a file (`> x.log 2>&1; echo $? > x.rc`, read `x.rc`), never through a pipe.

- [ ] `python ecossistema.py orchestrate <plan> --ambiente <env> --dry-run` exit 0 and `<plan-folder>/.orca-flight-plan.json` exists.
- [ ] The user's approval of that Flight Plan is a real message in this session, not inferred.
- [ ] Every table/front name equals a `rotulo` in `.orca-flight-plan.json`.
- [ ] Per front: `python ecossistema.py audit` exit 0 inside the table before cherry-pick.
- [ ] `git worktree list` shows no table of this plan left after cleanup (or the user chose Sleep).

## References

- `references/orca-app.md`: the ORCA app execution procedure (tables, launch, send, monitor, audit, integrate, clean up).
