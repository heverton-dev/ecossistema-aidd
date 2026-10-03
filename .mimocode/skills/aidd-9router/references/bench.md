# 9Router coding bench (2026-10-03)

Same prompt to every model, `stream:false`, token saver off, code checked by real tests.
- Easy task: `parse_duration` (13 tests). 21 models answered; all scored 13/13.
- Hard task: `calc` expression parser without eval (21 tests).

## Combos (revised after the harness test)

| Combo | Order (fallback) |
|---|---|
| `code-pro` | ag/claude-opus-4-6-thinking, ag/claude-sonnet-4-6, kr/claude-sonnet-4.5, ag/gemini-3.8-flash-low |
| `code-fast` | ag/gemini-3.8-flash-low, kr/qwen3-coder-next, kr/claude-haiku-4.5, xmtp/mimo-v2.6-flash |
| `code-free` | kr/qwen3-coder-next, kr/claude-haiku-4.5, kr/glm-5, agnes/agnes-3.0-flash |

`ag/*` and `xmtp/*` are paid plans; `kr/*` (Kiro) uses monthly free credits; `agnes/*` is free.

## Harness test (Claude Code `-p`, Read tool on AGENTS.md, answer first heading)

Passed: ag/gemini-3.8-flash-low 12 s, ag/claude-sonnet-4-6 14 s, ag/claude-opus-4-6-thinking 16 s, kr/claude-haiku-4.5 12 s, kr/claude-sonnet-4.5 16 s, kr/qwen3-coder-next 9 s, kr/glm-5 17 s, xmtp/mimo-v2.6-flash 15 s, kr/minimax-m2.5 21 s, agnes/agnes-3.0-flash 55 s.
Failed: groq/openai/gpt-oss-120b (413, 8000 tokens/min), cf/@cf/qwen/qwen2.5-coder-32b-instruct (prompt too long), ag/gpt-oss-120b-medium (500).

## Hard task ranking

| Model | Score | Time | Real input | Output |
|---|---|---|---|---|
| groq/openai/gpt-oss-120b | 21/21 | 8 s | 235 | 2642 |
| ag/gemini-3.8-flash-low | 21/21 | 12 s | 167 | 1320 |
| ag/claude-opus-4-6-thinking | 21/21 | 20 s | 194 | 1460 |
| ag/gpt-oss-120b-medium | 21/21 | 24 s | 231 | 2603 |
| kr/minimax-m2.5 | 21/21 | 55 s | 9719 | 5396 |
| kr/qwen3-coder-next | 20/21 | 9 s | 19613 | 1174 |
| kr/claude-haiku-4.5 | 20/21 | 9 s | 5079 | 724 |
| agnes/agnes-3.0-flash | 20/21 | 13 s | 238 | 901 |
| ag/claude-sonnet-4-6 | 20/21 | 15 s | 194 | 1120 |
| kr/glm-5 | 20/21 | 24 s | 5143 | 1314 |
| xmtp/mimo-v2.5-pro | 20/21 | 115 s | 415 | 4222 |
| kr/claude-sonnet-4.5 | 19/21 | 11 s | 5022 | 705 |
| cf/@cf/qwen/qwen2.5-coder-32b-instruct | 17/21 | 17 s | 193 | 493 |
| kr/deepseek-3.2 | 17/21 | 42 s | 4043 | 1411 |
| mistral/codestral-latest | 3/21 | 7 s | 176 | 673 |
| kgw/kilo-auto/free | 0/21 | 24 s | 203 | 1022 (broken indentation) |
| gemini/gemini-3.8-flash | 0/21 | 36 s | 8003 | stopped at max_tokens |
| ag/gemini-3.1-pro-low | 0/21 | 68 s | 7844 | stopped at max_tokens |
| ag/gemini-3.8-flash | 0/21 | 69 s | 15891 | stopped at max_tokens |
| xmtp/mimo-v2.6-pro, xmtp/mimo-v2.6-flash | - | >150 s | - | timeout |

Revised combos end to end (hard task): code-pro 21/21 in 20 s, code-fast 21/21 in 11 s, code-free 20/21 in 11 s.

## Unavailable on 2026-10-03

- No credits (402): all `kimchi/*`, `bzl/*`, `llm7/*`, `af/*`, `cerebras/gpt-oss-120b`.
- Retired or removed (404/410): `nvidia/z-ai/glm-5.2`, `nvidia/minimaxai/minimax-m3`, `ollama/glm-5`, `ollama/kimi-k2.5`, `cerebras/zai-glm-4.7`, `ps/laguna-s-2.1`, `kgw/kwaipilot/kat-coder-pro-v2.5:free`, `gemini/gemini-2.5-pro`.
- Subscription missing: `bpm/*`. Quota (429): `gemini/gemini-3.1-pro-preview`.
