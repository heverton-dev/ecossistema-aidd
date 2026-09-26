---
name: aidd-wizard
description: Generate an interactive bash wizard that walks a human through steps only they can perform. Use when provisioning infrastructure (VPS, Cloudflare), setting up credentials or CI secrets, walking a third-party dashboard, or running a one-off migration or cutover. Use only for steps the agent cannot perform itself.
---

# AIDD-Wizard — Steps Only the Human Can Do

A **wizard** is a bash script that walks a human, stage by stage, through a manual procedure: opens each URL, says exactly what to click and copy, captures the values, writes them where they belong (`.env`, GitHub secrets), confirms before irreversible actions, and shows progress. Secrets go from the dashboard straight into the file; they never pass through the chat.

Adapted from `wizard` in mattpocock/skills (commit c55ee46), MIT license. AIDD change: `open_url` also works in Git Bash on Windows (`cmd.exe` start).

The UX lives in [template.sh](template.sh): stage progress, confirmation gates, cross-platform URL opening (WSL, Git Bash, Linux, macOS), hidden secret entry, idempotent `.env` upserts, `gh secret`/`gh variable` writes, closing summary. Your job: scope the procedure and author its stages. The library above the `STAGES` marker is identical in every wizard; leave it as is.

A wizard is ephemeral by default: saved to a scratch path, deleted when done. Commit it only when the user wants a repeatable setup path in the repo.

## Process

### 1. Scope the procedure
List every manual step and every captured value. Read the repo first: `.env.example`, `README.md`, compose files, framework config, CI workflows (every `secrets.*` / `vars.*` reference is a value the wizard must produce). For a migration: current state, target state, irreversible actions between them.
Show the ordered stage list to the user and confirm; they may add, drop, reorder.
**Done when:** every stage is named in order, and for each value you know (a) where the human gets it, (b) where it is written (`.env`, GitHub secret, both, nowhere), (c) whether it is secret.

### 2. Map each stage's journey
Write the exact path per stage: URL, clicks, where the value shows, which variable it fills (e.g. "Dashboard → Developers → API keys → Reveal → copy"). Unknown UI or command: say so and ask the user or check the docs; write only steps you know exist.
**Done when:** a stranger could follow every stage.

### 3. Author the wizard
Copy `template.sh` to the target path. Replace the example stage with one `stage` per step, in dependency order. Helpers: `stage`, `say`/`step`, `open_url`, `ask`/`ask_secret`, `write_env`, `set_secret`/`set_var`, `pause`/`confirm`. Set `TOTAL_STAGES` to the number of stages.
Bar: open the URL before asking for its value; `ask_secret` for anything secret; `write_env` every persisted value; `set_secret` only what CI needs; `confirm` before any irreversible action; one focused task per stage.

### 4. Verify and hand off
- `bash -n <script>`; run `shellcheck` if available; `chmod +x <script>`.
- The agent never runs the wizard end to end: it opens browsers and blocks on human input. Trace it statically: every value from step 1 is captured and lands where step 1 said; every `set_secret` name matches a `secrets.*` reference in CI.
- Tell the user how to run it (Git Bash on Windows: `bash <script>`).
