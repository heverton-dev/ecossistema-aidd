# Harness routing and Orca ADE

Contents: 1. per harness · 2. Orca ADE · 3. not supported

## 1. Per harness (`scripts/harness_9router.py <harness>`)

| Harness | How "on" works | Tier mapping | Verified |
|---|---|---|---|
| claude | env `ANTHROPIC_BASE_URL`, `ANTHROPIC_AUTH_TOKEN`, `ANTHROPIC_DEFAULT_{OPUS,SONNET,HAIKU}_MODEL` | opus/sonnet/haiku; subagents and skills choose with `model:` | `claude -p`, Orca worker |
| opencode | env `OPENCODE_CONFIG_CONTENT` adds provider `aidd9r`; `-m aidd9r/code-fast` | `small_model` = code-free | `opencode run`, Orca worker |
| mimo | env `MIMOCODE_CONFIG_CONTENT` (same schema as OpenCode) | same as OpenCode | `mimo run`, interactive TUI shows `code-fast 9Router (aidd)` |
| omp | flags `--model/--smol/--plan/--slow aidd9r/*`; provider in `~/.omp/agent/models.yml` | default, smol, plan, slow | `omp -p`, Orca worker |

The key goes through the variable `NINEROUTER_KEY` (`{env:NINEROUTER_KEY}` in OpenCode/MiMo, `apiKey: NINEROUTER_KEY` in omp). omp runs on Bun, which also loads the `.env` of the current folder.

## 2. Orca ADE

- Settings > Agents > Command: `claude-9router`, `opencode-9router`, `mimo-9router`, `omp-9router` (wrappers from `scripts/instalar_wrappers.py`). The Orca terminal is Git Bash, so both the bash file and the `.cmd` exist.
- Orca's runtime method `settings.update` (named pipe in `%APPDATA%/orca/orca-runtime.json`) accepts `agentDefaultEnv` and `agentDefaultArgs`, not `agentCmdOverrides`. The Command field changes only in the UI (or with `orca computer set-value` on that field).
- Managed Claude accounts: Orca refuses to launch Claude when `agentDefaultEnv.claude` holds `ANTHROPIC_AUTH_TOKEN` or `ANTHROPIC_API_KEY`. Put only `NINEROUTER_*` there; the wrapper sets the Anthropic variables in the child process.
- Plain terminals do not receive agent Environment or Command; only agent launches (new agent tab, `orca orchestration worker-start --agent <id>`) do.
- Quick Commands "9Router ON/OFF/ESTADO" live in the terminal tab bar menu; run them in a shell tab, never inside an agent prompt.
- MiMo supervised workers fail Orca's readiness check (`agent_readiness timeout`) even with the original `mimo` command; MiMo works when opened as a normal agent tab. A remote MCP that needs login (Cloudflare) shows a blocking dialog on MiMo start until `mimo mcp auth <server>` is done once.

## 3. Not supported

- Gemini CLI: speaks only Google's API format; untested through 9Router.
- Antigravity (agy): only through 9Router's MITM/DNS interception, which is invasive. 9Router already uses the Antigravity account as a provider.
- Cursor: requests leave from Cursor's servers, so only the public VPS URL works.
