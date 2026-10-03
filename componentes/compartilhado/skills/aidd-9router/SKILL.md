---
name: aidd-9router
description: House calibration for calling the 9Router AI gateway at minimum token cost - which combo to pick for coding (code-pro, code-fast, code-free), when to disable the token saver, stream and max_tokens rules, and how to read the inflated usage numbers. Use when a task sends prompts, code generation or delegated subtasks through 9Router, NINEROUTER_URL or NINEROUTER_KEY, or when the user asks which 9Router model or combo to use. Also covers image, text-to-speech, speech-to-text, embeddings, web search and web fetch through 9Router.
---

# aidd-9router

9Router is the OpenAI-compatible gateway, running 24/7 on the VPS at `https://9router.vpsconexao.org` (Swarm stack `ninerouter`; `NINEROUTER_URL` in `.env`). A local copy at `http://localhost:20128` is only a fallback with its own separate database. This skill holds the house rules measured on 2026-10-03. Non-chat endpoints (image, TTS, STT, embeddings, web search, web fetch): `references/endpoints.md`.

## 1. Config

- `.env` holds `NINEROUTER_URL` and `NINEROUTER_KEY` (dashboard "Endpoint & Key", key `aidd`). Never print the key.
- "Require API key" is ON: `/v1/chat/completions` without the key returns 401. `/v1/models` stays public.
- Health: `curl $NINEROUTER_URL/api/health` returns `{"ok":true}`. Done when it does.

## 2. Pick the model

| Need | Model | Claude Code tier | Measured (hard parser task, 21 tests) |
|---|---|---|---|
| Quality first | `code-pro` | opus | 21/21, ~20 s |
| Speed, default | `code-fast` | sonnet | 21/21, ~11 s |
| Zero cost | `code-free` | haiku | 20/21, ~11 s |

Combos fall back in order when a provider fails. Members and full ranking: `references/bench.md`.

Every combo member passed a real Claude Code tool-use run (read a file, answer). Excluded from combos:
- `groq/*` free tier: 8000 tokens/min, a harness prompt gets 413 and 9Router does not fall back on 413.
- `cf/*` (32k context) and `ag/gpt-oss-120b-medium` (500 errors).

Avoid for token economy in direct calls:
- `kr/*` (Kiro) injects 3k-20k hidden input tokens per call.
- `gemini/*` and `ag/gemini-3.8-flash` (non `-low`) burn 5k-15k reasoning tokens and can stop at `max_tokens` with no code.
- `xmtp/mimo-*-pro` think for 60-120 s.

## 3. Call it

Run the script instead of hand-writing curl:

```bash
python componentes/compartilhado/skills/aidd-9router/scripts/chamar.py "<prompt>" --modelo code-fast
```

Done when it exits 0. Exit 2 means the answer is still truncated after one retry; split the task.

The script applies these rules (follow them when calling by hand):
1. Always send `"stream": false`. The default is SSE and a plain JSON parse fails.
2. Set `max_tokens` to the expected answer size plus reasoning margin: 512 short, 2048 code, 8000 for reasoning models.
3. If `finish_reason` is `length`, retry once with double `max_tokens`.
4. Short answers: send header `X-9Router-Token-Saver: off`. Long answers (above ~300 tokens): leave the saver on (`--longo`) so Caveman compresses the output.

## 4. Route a harness through the combos

Claude Code, on/off per session (no settings file changes):

```bash
python componentes/compartilhado/skills/aidd-9router/scripts/claude_9router.py   # on
claude                                                                           # off
python componentes/compartilhado/skills/aidd-9router/scripts/claude_9router.py --mapa
```

Inside Orca ADE (verified with a supervised Claude worker), set in Settings > Agents > Claude:
- Command: `claude-9router` (wrapper in `~/.local/bin`, a bash file and a `.cmd`, both calling this launcher). Keep it there; toggle with the Orca Quick Commands "9Router ON" / "9Router OFF" / "9Router ESTADO" (`claude-9router --ligar`, `--desligar`, `--estado`). Off creates `~/.aidd/9router-desligado` and the wrapper starts plain `claude`.
- Environment: `NINEROUTER_URL`, `NINEROUTER_KEY`, `NINEROUTER_OPUS/SONNET/HAIKU`. Never put `ANTHROPIC_AUTH_TOKEN` there: Orca's managed Claude accounts refuse that launch.
- Arguments: `--model sonnet` so the default tier is `code-fast`.

The launcher maps tiers: opus -> `code-pro`, sonnet -> `code-fast`, haiku -> `code-free`. Subagents and skills pick a tier with their `model:` field, so each task lands on its combo. Override one tier with `NINEROUTER_OPUS`, `NINEROUTER_SONNET` or `NINEROUTER_HAIKU` in `.env`. The ecosystem keeps the delegated protocol: it asks the harness, the harness answers through the combo.

## 5. Read usage correctly

- 9Router adds a fixed **+2000** to `prompt_tokens`, `input_tokens` and `total_tokens` in every response. These tokens are never sent to the model. Real input = reported - 2000.
- Real saver overhead (Caveman Ultra only): ~385 input tokens per call.
- Dashboard "cost" uses the inflated numbers.

## 6. Token Saver settings (dashboard "Economizador de Tokens")

| Setting | State | Why |
|---|---|---|
| RTK | on | Lossless compression of tool output, adds nothing. |
| Headroom | off | The service on :8787 is not running, so it saved nothing. |
| Caveman | on, Ultra | Pays off on long answers; skip it per call with the header. |
| Ponytail | off | Coding style comes from the harness; it cost ~370 tokens per call. |

Done when `GET /api/settings` (logged-in dashboard) shows `rtkEnabled:true, headroomEnabled:false, cavemanEnabled:true, ponytailEnabled:false`.
