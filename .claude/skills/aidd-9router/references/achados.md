# Findings (verified 2026-10-03)

| Finding | Evidence | Rule |
|---|---|---|
| 9Router adds a fixed +2000 to `prompt_tokens`, `input_tokens`, `total_tokens` | Ollama log: 11 real vs 2011 reported; normalizer in the server bundle adds `2e3` | Real input = reported - 2000; dashboard cost is inflated |
| Caveman Ultra + Ponytail Ultra cost ~757 real input tokens per call | Ollama: 768 with savers, 12 without | Ponytail off; saver off on short calls |
| Kiro (`kr/*`) injects 3k-20k hidden input tokens | bench: 4k-19k real input for a 200-token prompt | Use Kiro where free credits matter more than tokens |
| Groq free tier: 413 above 8000 tokens/min, no fallback | Claude Code prompt alone exceeds it | Never in harness combos |
| Reasoning Gemini models (`gemini/*`, `ag/gemini-3.8-flash`) spend 5k-15k thinking tokens and stop at `max_tokens` without code | bench hard task | Use `ag/gemini-3.8-flash-low` |
| Default response is SSE | first test returned `data:` lines | Always `"stream": false` in scripts |
| Orca refuses Claude launch with Anthropic auth env when managed accounts are on | `This Claude launch defines explicit Anthropic auth environment variables` | Wrapper sets them in the child process |
| One invalid provider disables all custom providers in omp | `models.yml validation failed - custom providers disabled` | Local Ollama needs `auth: none` and `api` |
| `components sync` left files removed from the source in harness copies | verify flagged orphans after a clean sync | Fixed: sync now removes them inside the component folder |
| Reading Orca settings through the accessibility tree prints env values (the key) | key shown in tool output | Read Orca settings with `orca_9router.py --estado`, which masks the key |
