# ORCA app execution procedure

This CLI never executes anything in the ORCA environment: the session assistant drives the real app through `orca-cli`, after `python ecossistema.py plan iniciar-execucao <plan-path>`.

## Step 0: load the manual of the installed version

```bash
orca skills get orca-cli
```

Flags change between versions. Never guess a subcommand or flag from memory; the exact syntax always comes from the guide printed now.

## For each front of `.orca-flight-plan.json`, in order

1. **Make sure the repository is registered** in ORCA (list first; register only if missing).
2. **Create the front's table in one command**, with agent and prompt:
   `worktree create --name <front-label> --no-parent --agent <harness> --prompt "<front text>" --json`
   (`<front-label>` is the `rotulo` field, e.g. `PLAN-0016-fase-04-eliminar-timesleep-injetar`). Use `--parent-worktree` only if the user asked for stacked work.
3. **Never launch the harness with `--resume <session-id>`.** Each front is a new session. When the old transcript is gone the harness dies with `No conversation found with session ID` and the table looks alive with no AI inside (4 of 5 tables once hung this way).
4. **Only if a custom argv is needed** (model or effort that `--agent` does not cover), use the two-step path with the mandatory lock:
   - `terminal create --worktree id:<repoId>::<path> --command '<harness ...>' --json`
   - `terminal wait --terminal <handle> --for tui-idle --timeout-ms 60000 --json`
   - Send the prompt only if the wait result has `satisfied: true`. A timed-out wait also prints a normal result: read the field. If `false`, retry the wait once with a longer timeout; if still `false`, report the front as not started and send nothing.
   - `terminal send --terminal <handle> --text "<front text>" --enter --wait-submit 10 --json`
5. **Never resend silently.** `accepted: true` proves the input was accepted, not that the turn started; the `turn_started` stage of the receipt (`--wait-submit`) proves it. On an ambiguous transport failure repeat the SAME command with the `--retry-request <id>` from the receipt. Empty "reinforcement" sends are forbidden (they duplicate prompts and cause loops).
6. **Monitor periodically**, not only at the end: `terminal read` with a cursor, and the table panel to catch a stuck or forgotten AI early.
7. **Never invent intermediate approval.** If a front fails or hangs, stop and tell the user before the next one.
8. **Real audit before integrating:** run `python ecossistema.py audit` (or `pre-commit run --all-files`) inside the table, plus real tests, `git status`/`git diff`, reading the changed files and running the app. Never trust only the table AI's word.
9. **Integrate:** bring the approved commit to the main branch (e.g. `cherry-pick`), resolving real conflicts while keeping both fronts' changes when it makes sense.
10. **Clean up (always, even if the front failed):** close the table's terminals and remove the table. If the front continues later, use workspace Sleep instead of closing.
