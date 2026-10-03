# 9Router endpoints (non-chat)

Condensed from the vendor skills (decolua/9router `skills/9router-*`). All calls: `Authorization: Bearer $NINEROUTER_KEY`.
Discover models per kind: `GET /v1/models/<kind>` with kind = `image`, `tts`, `stt`, `embedding`, `web`, `image-to-text`. Params of one model: `GET /v1/models/info?id=<model>`.

| Capability | Endpoint | Required fields | Useful options |
|---|---|---|---|
| Image | `POST /v1/images/generations` | `model`, `prompt` | `size`, `n`, `quality`, `response_format=url\|b64_json`; query `?response_format=binary` returns raw bytes |
| Text to speech | `POST /v1/audio/speech` | `model` (voice id), `input` | voices: `GET /v1/audio/voices?provider=edge-tts&lang=pt`; default raw mp3, `?response_format=json` gives base64 |
| Speech to text | `POST /v1/audio/transcriptions` (multipart) | `model`, `file` | `language`, `prompt`, `response_format=json\|text\|verbose_json\|srt\|vtt` |
| Embeddings | `POST /v1/embeddings` | `model`, `input` (string or list) | `encoding_format`, `dimensions` (OpenAI v3) |
| Web search | `POST /v1/search` | `model` (ids end in `/search`, kind `webSearch`), `query` | `max_results` (5), `search_type=web\|news\|x`, `country`, `language`, `time_range` |
| Web fetch | `POST /v1/web/fetch` | `model` (ids end in `/fetch`, kind `webFetch`), `url` | `format=markdown\|text\|html`, `max_characters` |

Example (save an image):

```bash
curl -X POST "$NINEROUTER_URL/v1/images/generations?response_format=binary" \
  -H "Authorization: Bearer $NINEROUTER_KEY" -H "Content-Type: application/json" \
  -d '{"model":"<id from /v1/models/image>","prompt":"watercolor mountains","size":"1024x1024"}' --output out.png
```

Errors: 401 bad or missing key; 400 `Invalid model format` means the id is not in `/v1/models/<kind>`; 503 `All accounts unavailable` means wait `retry-after` or add a provider account.
