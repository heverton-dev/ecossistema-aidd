---
name: aidd-bridge
description: Runs the atomic aidd-bridge tool operations that free low-code projects (Lovable, v0, Bolt) for self-hosting - scan, Supabase-to-PostgreSQL conversion, app merge and VPS packaging. Use when the user asks for one bridge step, or says "bridge", "/bridge", "scan do lovable", "converter banco", "empacotar para VPS". For the full Flow 03 use aidd-freedom.
---

# aidd-bridge

Atomic operations of `tools/aidd-bridge`. The full Flow 03 (`[FORGE -> PLANNER] -> BRIDGE -> [MASTER -> ENTERPRISE -> OPS]`) is `aidd-freedom`.

- Ingest and scan Lovable/Vite/React repositories.
- Sanitize Supabase migrations into plain PostgreSQL and PostgREST.
- Merge 2 to 4 apps into one monorepo with unified Tailwind.
- Generate Dockerfile, Docker Compose and Caddy reverse proxy with automatic HTTPS.

## Run

```bash
python ecossistema.py bridge scan [path]
python ecossistema.py bridge convert-db [path]
python ecossistema.py bridge merge [app1] [app2] --output [destination]
python ecossistema.py bridge pack [path] --domain example.com
```

Slash command: `/bridge <scan|convert-db|merge|pack> ...`.
Passing `--nome`, `--pasta`, `--slug` or `--dry-run` to `bridge` redirects to the full Flow 03 (`freedom`).

Done when: each operation exits 0.
