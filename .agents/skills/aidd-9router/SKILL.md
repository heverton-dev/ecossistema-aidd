---
name: aidd-9router
description: Builds, calibrates, deploys and operates the house 9Router AI gateway end to end - token saver tuning, coding combos (code-pro, code-fast, code-free) chosen by real benchmarks, 24/7 deploy on the VPS with DNS, routing of Claude Code, OpenCode, MiMo and omp through the combos inside Orca ADE with an on/off switch, health diagnosis and cheap direct calls. Use when the user mentions 9Router, NINEROUTER_URL, NINEROUTER_KEY, combos, routing a harness or Orca agents through 9Router, deploying or checking the gateway, or which model to use for coding; also for image, TTS, STT, embeddings and web search/fetch through 9Router.
---

# aidd-9router

9Router is the OpenAI/Anthropic-compatible gateway: one key, many providers, fallback combos. The house instance runs 24/7 at `https://9router.vpsconexao.org` (Swarm stack `ninerouter`); `NINEROUTER_URL` in `.env` points to it. All scripts live in `scripts/` (run from the repo root, `python componentes/compartilhado/skills/aidd-9router/scripts/<script>`), read `.env` themselves and never print secrets.

Start every task with `doctor.py`. Done when it prints `RESULTADO: ok` (exit 0).

## 1. Use it (most tasks)

| Need | Run | Done when |
|---|---|---|
| Ask a model once, cheap | `chamar.py "<prompt>" --modelo code-fast` | exit 0 (2 = still truncated, split the task) |
| Health of everything | `doctor.py` (`--rapido` skips chat calls) | `RESULTADO: ok` |
| Image, TTS, STT, embeddings, web search/fetch | endpoints in `references/endpoints.md` | HTTP 200 |

Pick the combo: `code-pro` (quality, ~20 s), `code-fast` (default, ~11 s), `code-free` (zero cost, Kiro credits). Ranking and members: `references/bench.md`.

Call rules (built into `chamar.py`): `"stream": false`; `max_tokens` sized to the answer (512 short, 2048 code, 8000 reasoning); retry once with double on `finish_reason: length`; header `X-9Router-Token-Saver: off` on short answers. Real input tokens = reported `prompt_tokens` - 2000 (9Router inflates the number; nothing extra reaches the model).

## 2. Route harnesses through the combos

Tiers: opus/plan -> `code-pro`, sonnet/default -> `code-fast`, haiku/smol -> `code-free` (override with `NINEROUTER_OPUS/SONNET/HAIKU` in `.env`). The ecosystem keeps the delegated protocol: it asks the harness, the harness answers through the combo.

1. `instalar_wrappers.py` - creates `claude-9router`, `opencode-9router`, `mimo-9router`, `omp-9router` (bash + `.cmd`) in `~/.local/bin`. Done when exit 0.
2. `omp_provider.py` - adds provider `aidd9r` to `~/.omp/agent/models.yml` and checks omp loads it. Done when exit 0.
3. `orca_9router.py --aplicar` - Orca Environment and Arguments of Claude plus Quick Commands "9Router ON/OFF/ESTADO". Exit 2 lists agents whose Command must still be set in Settings > Agents > Command to the wrapper name. Done when `orca_9router.py --estado` exits 0.
4. Switch: Quick Commands in the terminal tab bar, or `harness_9router.py --ligar | --desligar | --estado`. Off starts every harness untouched.
5. Prove it: `bench.py harness sonnet` - done when `"passou": true` and `"usou": ["code-fast"]`.

Never put `ANTHROPIC_AUTH_TOKEN` in Orca's agent Environment (managed Claude accounts refuse the launch). Details, MiMo and unsupported harnesses: `references/harnesses.md`.

## 3. Build or rebuild the gateway

1. Local install, key `aidd`, "Exigir chave de API" on, token saver (RTK on, Headroom off, Caveman Ultra on, Ponytail off): `references/setup.md` sections 1-2. Done when chat without key returns 401 and with key returns 200.
2. Combos: choose members only among models that pass both `bench.py codigo <id>` (21/21) and `bench.py harness <id>`; create them with the dashboard snippets in `references/setup.md` section 4. Done when each combo passes both benches.
3. Deploy: `deploy_vps.py --dry-run`, then `deploy_vps.py` (copies providers, keys and combos; creates volume, stack and DNS; waits for health). Done when it prints `no ar:`. Then set `NINEROUTER_URL` to the VPS, re-run `orca_9router.py --aplicar` and `doctor.py`. Operations, rollback and dashboard login: `references/deploy-vps.md`.

## 4. Before changing anything

Read `references/achados.md`: measured traps (+2000 usage, Kiro hidden prompt, Groq 413 without fallback, reasoning models stopping at `max_tokens`, Orca managed accounts, invalid omp provider disabling all providers). Asset: `assets/ninerouter-stack.yml` (stack template filled by `deploy_vps.py`).

## Negative Guardrails

- NEVER wire `chamar.py` or `NINEROUTER_KEY` into an ecosystem pipeline as its LLM (pure, open, delegated protocol): the model is always the running harness; 9Router only sits behind the harness wrapper.
- NEVER print, paste or commit `NINEROUTER_KEY`, nor read Orca settings through the accessibility tree: use `orca_9router.py --estado`, which masks the key.
- NEVER put `ANTHROPIC_AUTH_TOKEN` in Orca's agent Environment: managed accounts refuse the launch; `claude-9router` sets it only in the child process.
- NEVER run `deploy_vps.py --sobrescrever-dados` or remove the volume without the user's OK: it replaces the VPS database (providers, OAuth tokens, keys, combos).
- NEVER add a combo member that did not pass both `bench.py codigo <id>` (21/21) and `bench.py harness <id>`, nor a Groq free model in a harness combo (413 above 8000 tokens/min, no fallback).

## Failure Modes & Fallback

- **`doctor.py` prints `RESULTADO: FALHA crítica`:** `harness_9router.py --desligar` so harnesses start untouched, then fix the failing check from `references/achados.md`.
- **`chamar.py` exit 2 (still truncated):** split the task; do not keep doubling `max_tokens` on reasoning models.
- **`deploy_vps.py` `ERRO etapa <n>`:** `docker service logs --tail 50 ninerouter_ninerouter`; rollback `docker stack rm ninerouter` (the volume stays).
- **`orca_9router.py --aplicar` exit 2:** set the listed agents' Command to the wrapper name in Settings > Agents > Command, then `--estado`.

## Stopping Checklist

Prove each item with the exit code read from a file (`> x.log 2>&1; echo $? > x.rc`, read `x.rc`), never through a pipe.

- [ ] `python componentes/compartilhado/skills/aidd-9router/scripts/doctor.py` exit 0 with `RESULTADO: ok`.
- [ ] `orca_9router.py --estado` exit 0 when Orca routing was touched.
- [ ] `bench.py harness sonnet` shows `"passou": true` and `"usou": ["code-fast"]` when routing was changed.
- [ ] `git diff` and the transcript hold no `NINEROUTER_KEY` value.
