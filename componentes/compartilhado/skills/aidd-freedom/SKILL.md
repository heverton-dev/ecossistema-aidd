---
name: aidd-freedom
description: Runs Triad Flow 03 (low-code liberation) end to end - removes Lovable, v0 or Bolt vendor lock-in, migrates Supabase to PostgreSQL through the aidd-freedom engine while keeping the UI, then master, enterprise and ops; also runs single engine steps (scan, convert-db, merge, pack). Use when the user wants to free or self-host a low-code app or asks for one of those steps, or types "/freedom", "freedom", "freedom-motor", "/bridge", "bridge", "libertar app lovable", "desacoplar app low-code", "migrar v0 ou bolt para postgresql", "scan do lovable", "converter banco", "empacotar para VPS".
---

# aidd-freedom (Flow 03, low-code liberation)

Pipeline: `[FORGE -> PLANNER] -> FREEDOM -> [MASTER -> ENTERPRISE -> OPS]`

| Stage | Tool | Output |
|---|---|---|
| Foundation | `aidd-forge` | environment shielding and git hooks |
| Planning | `aidd-planner` | data schemas and routes |
| Engine | `aidd-freedom` (`tools/aidd-freedom`) | anti-lock-in scan, Supabase removal, PostgreSQL migration, original visual identity kept |
| Harmonization | `aidd-master` | exported frontend wired to the modular Python API |
| Shielding | `aidd-enterprise` | SHA-256 shielding and drift detection |
| Infrastructure | `aidd-ops` | full containerization with Nginx and database |

`freedom-motor` with project flags (`--nome`, `--pasta`, `--slug`, `--dry-run`) also routes here; `freedom-motor <operation>` runs a single engine step (see below).

## Steps

1. Get the export folder (Lovable, v0, Bolt) and the project name. Done when the export folder exists.
2. Simulate first:
   ```bash
   python ecossistema.py freedom ./exports/lovable-app --dry-run
   ```
3. Run:
   ```bash
   python ecossistema.py freedom ./exports/lovable-app "App Hub"
   # explicit flags
   python ecossistema.py freedom --nome "App Hub" --slug app-hub --dominio saas --pasta ./projetos/app-hub --origem ./exports/lovable-app
   # same engine
   python ecossistema.py run-fluxo --fluxo freedom --nome "App Hub" --slug app-hub --dominio saas --pasta ./projetos/app-hub --origem ./exports/lovable-app
   ```
   Positional form: `<export_path> [name] [domain]`. Done when the command exits 0.
4. Confirm the Supabase/BaaS client calls were replaced by the clean API, the UI is unchanged, and the delivery honors the Quarteto Sine Qua Non defined in `AGENTS.md` section 3.

## Engine invariants (`run-fluxo`)

- Synchronous: no stage starts before the previous one exits 0.
- Handoffs validated by JSON Schema (`componentes/compartilhado/specs/handoff-*.schema.json`).
- Fail-fast: any gate break stops the pipeline.
- Writes `ORQUESTRACAO_EXECUCAO.json` in the target folder.

## Engine only (`freedom-motor`)

Atomic operations of `tools/aidd-freedom`: ingest and scan Lovable/Vite/React repositories; sanitize Supabase migrations into plain PostgreSQL and PostgREST; merge 2 to 4 apps into one monorepo with unified Tailwind; generate Dockerfile, Docker Compose and Caddy reverse proxy with automatic HTTPS.

```bash
python ecossistema.py freedom-motor scan [path]
python ecossistema.py freedom-motor convert-db [path]
python ecossistema.py freedom-motor merge [app1] [app2] --output [destination]
python ecossistema.py freedom-motor pack [path] --domain example.com
```

Old name `bridge` (and `/bridge`) still works for one cycle and prints an "old name" warning (table in `componentes/compartilhado/specs/NOMES-ANTIGOS.json`).
Done when: each operation exits 0.
