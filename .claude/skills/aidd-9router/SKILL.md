---
name: aidd-9router
description: House calibration for calling the local 9Router AI gateway at minimum token cost - which combo to pick for coding (code-pro, code-fast, code-free), when to disable the token saver, stream and max_tokens rules, and how to read the inflated usage numbers. Use when a task sends prompts, code generation or delegated subtasks through 9Router, NINEROUTER_URL or NINEROUTER_KEY, or when the user asks which 9Router model or combo to use. For raw endpoint formats (image, TTS, STT, embeddings, web search/fetch) use the vendor skills 9router-*.
---

# aidd-9router

9Router is the local gateway (`http://localhost:20128`, OpenAI-compatible). The vendor skills `9router` and `9router-*` describe the endpoints; this skill holds the house rules measured on 2026-10-03.

## 1. Config

- `.env` holds `NINEROUTER_URL` and `NINEROUTER_KEY` (dashboard "Endpoint & Key", key `aidd`). Never print the key.
- "Require API key" is ON: `/v1/chat/completions` without the key returns 401. `/v1/models` stays public.
- Health: `curl $NINEROUTER_URL/api/health` returns `{"ok":true}`. Done when it does.

## 2. Pick the model

| Need | Model | Measured (hard parser task, 21 tests) |
|---|---|---|
| Quality first | `code-pro` | 21/21, ~17 s |
| Speed, default | `code-fast` | 21/21, ~6 s |
| Zero cost | `code-free` | 21/21, ~6 s |

Combos fall back in order when a provider fails. Members and full ranking: `references/bench.md`.

Avoid for token economy:
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

## 4. Read usage correctly

- 9Router adds a fixed **+2000** to `prompt_tokens`, `input_tokens` and `total_tokens` in every response. These tokens are never sent to the model. Real input = reported - 2000.
- Real saver overhead (Caveman Ultra only): ~385 input tokens per call.
- Dashboard "cost" uses the inflated numbers.

## 5. Token Saver settings (dashboard "Economizador de Tokens")

| Setting | State | Why |
|---|---|---|
| RTK | on | Lossless compression of tool output, adds nothing. |
| Headroom | off | The service on :8787 is not running, so it saved nothing. |
| Caveman | on, Ultra | Pays off on long answers; skip it per call with the header. |
| Ponytail | off | Coding style comes from the harness; it cost ~370 tokens per call. |

Done when `GET /api/settings` (logged-in dashboard) shows `rtkEnabled:true, headroomEnabled:false, cavemanEnabled:true, ponytailEnabled:false`.
