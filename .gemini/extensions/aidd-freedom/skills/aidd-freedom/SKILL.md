---
name: aidd-freedom
description: Runs Triad Flow 03 (low-code liberation) end to end - removes Lovable, v0 or Bolt vendor lock-in, migrates Supabase to PostgreSQL through aidd-bridge while keeping the UI, then master, enterprise and ops. Use when the user wants to free or self-host a low-code app, or types "/freedom", "freedom", "libertar app lovable", "desacoplar app low-code", "migrar v0 ou bolt para postgresql". For a single bridge step use aidd-bridge.
---

# aidd-freedom (Flow 03, low-code liberation)

Pipeline: `[FORGE -> PLANNER] -> BRIDGE -> [MASTER -> ENTERPRISE -> OPS]`

| Stage | Tool | Output |
|---|---|---|
| Foundation | `aidd-forge` | environment shielding and git hooks |
| Planning | `aidd-planner` | data schemas and routes |
| Engine | `aidd-bridge` | anti-lock-in scan, Supabase removal, PostgreSQL migration, original visual identity kept |
| Harmonization | `aidd-master` | exported frontend wired to the modular Python API |
| Shielding | `aidd-enterprise` | SHA-256 shielding and drift detection |
| Infrastructure | `aidd-ops` | full containerization with Nginx and database |

`/bridge` with project flags (`--nome`, `--pasta`, `--slug`, `--dry-run`) also routes here; plain `/bridge <operation>` is `aidd-bridge`.

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
