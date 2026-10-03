# 9Router setup and calibration

Contents: 1. install and key · 2. token saver · 3. combos · 4. dashboard API from the browser

## 1. Install and key

- Local install: `npm i -g 9router` (verified 0.5.95), dashboard at `http://localhost:20128/dashboard`, data in `%APPDATA%/9router` (Windows) or `~/.9router`.
- Dashboard > "Endpoint & Key": create key `aidd`, turn ON "Exigir chave de API". Chat without the key returns 401; `/v1/models` is public locally and protected on the VPS.
- `.env` section 17: `NINEROUTER_URL`, `NINEROUTER_KEY`, optional `NINEROUTER_OPUS/SONNET/HAIKU`. Provider keys (Gemini, Xiaomi, Kiro OAuth) live only inside 9Router, never in the repo.

## 2. Token saver (dashboard "Economizador de Tokens")

Measured with local Ollama (real tokens from its server log) on 2026-10-03:

| Setting | Decision | Reason |
|---|---|---|
| RTK | on | lossless compression of tool output, zero overhead |
| Headroom | off | needs a separate service on :8787; when stopped it saves nothing and adds a failed call |
| Caveman | on, Ultra | ~385 real input tokens per call; pays off on answers above ~300 tokens |
| Ponytail | off | ~370 tokens per call; coding style comes from the harness |

Per call: header `X-9Router-Token-Saver: off` skips all savers (use it on short calls). The `[ml]` Headroom extra pulls ~1 GB (torch); uninstall it only if no other tool in the same Python uses torch.

## 3. Combos

Rules learned from the bench (`references/bench.md`):
- Every member must pass the harness test (`scripts/bench.py harness <model>`): large prompt plus tool calls. Free Groq (8000 tokens/min, 413) and Cloudflare Workers AI (32k context) fail, and 9Router does not fall back on 413.
- Order members by quality, then speed; put free-credit providers (Kiro) where their hidden prompt (3k-20k tokens) is acceptable.
- Keep only `code-pro`, `code-fast`, `code-free` so every harness maps tiers the same way.

## 4. Dashboard API from the browser

Combos and settings need the dashboard login cookie (the API key is not accepted). Open the dashboard logged in and run in the page console (or through the Chrome automation tool):

```js
await fetch('/api/settings',{method:'PATCH',headers:{'Content-Type':'application/json'},
  body:JSON.stringify({rtkEnabled:true,headroomEnabled:false,cavemanEnabled:true,cavemanLevel:'ultra',ponytailEnabled:false})});
await fetch('/api/combos',{method:'POST',headers:{'Content-Type':'application/json'},
  body:JSON.stringify({name:'code-fast',models:['ag/gemini-3.8-flash-low','kr/qwen3-coder-next','kr/claude-haiku-4.5','xmtp/mimo-v2.6-flash']})});
await fetch('/api/combos/<id>',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:'code-fast',models:[/*...*/]})});
await fetch('/api/combos/<id>',{method:'DELETE'});
(await fetch('/api/combos').then(r=>r.json())).combos.map(c=>c.name+': '+c.models.join(' > '));
```

Never print the response of `/api/settings` whole: it carries secrets. Read single fields.
