---
name: aidd-freedom
description: Runs Triad Flow 03 (low-code liberation) end to end - removes Lovable, v0 or Bolt vendor lock-in, migrates Supabase to PostgreSQL through the aidd-freedom engine while keeping the UI, then master, enterprise and ops; also runs single engine steps (scan, convert-db, merge, pack). Use when the user wants to free or self-host a low-code app or asks for one of those steps, or types "/freedom", "freedom", "freedom-motor", "/bridge", "bridge", "libertar app lovable", "desacoplar app low-code", "migrar v0 ou bolt para postgresql", "scan do lovable", "converter banco", "empacotar para VPS".
---

# aidd-freedom (Flow 03, low-code liberation)

Pipeline: `[FORGE -> PLANNER -> MASTER -> DISPATCH] -> {ENGINE nas Worktrees} -> [BARREIRA (Rebase Sync) -> ENTERPRISE -> OPS -> 54 GATES]`

| Stage | Tool | Output |
|---|---|---|
| 1. Fundação | `aidd-forge` | blindagem de ambiente e hooks git |
| 2. Planejamento | `aidd-planner` | contratos BDD/SDD, esquemas de dados e rotas |
| 3. Fatiamento VSA | `aidd-master` | fatiamento vertical e contratos de fatias |
| 4. Despacho & Worktrees | `aidd-dispatch` | isolamento em git worktrees com micro-gates |
| 5. Motor | `aidd-freedom` (`tools/aidd-freedom`) | varredura anti-lock-in, migração PostgreSQL e preservação visual |
| 6. Barreira & Rebase | `aidd-master` | rebase determinístico e merge das fatias |
| 7. Blindagem | `aidd-enterprise` | auditoria SHA-256 e proteção corporativa |
| 8. Infraestrutura | `aidd-ops` | containerização completa, Nginx e banco de dados |
| 9. Qualidade Global | `54 Gates` | auditoria determinística final |

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

## Negative Guardrails

- NEVER modify or delete the original export folder (`--origem`): `freedom-motor convert-db <path>` writes `init-db.sql` inside `<path>` unless `--output` is given, so point it at the working copy.
- NEVER run `freedom-motor destroy` or pass `--yes` without explicit user OK: it removes the Swarm stack, volumes, Cloudflare DNS and the VPS folder, irreversibly.
- NEVER run `freedom-motor migrate-auth --apply` before showing the user the preview report from the run without `--apply`.
- NEVER change components, styles or Tailwind tokens of the exported UI: the flow keeps the original visual identity; only Supabase/BaaS calls are replaced.
- NEVER commit a fixed database password generated in `init-db.sql` or the compose; `G_SEGREDOS` already flagged the data bridge for this.

## Failure Modes & Fallback

- **`scan` finds 0 Supabase migrations:** the export is not Lovable/Vite or lacks `supabase/migrations`; ask the user for the full export before `convert-db`.
- **Generated slice tests fail after `scan`:** fix the converted slice under `src/modules/<domain>/` and rerun `scan`; never delete the failing test.
- **`destroy` exits 1 ("ERRO VPS"):** stop; report the VPS error to the user and do not retry with other credentials.
- **`merge` with more than 4 apps or conflicting routes:** stop and ask the user which apps and routes win.

## Stopping Checklist

- [ ] `python ecossistema.py freedom --nome "<Name>" --slug <slug> --dominio <domain> --pasta <dest> --origem <export> > fr.log 2>&1; echo $? > fr.rc` and `fr.rc` holds `0`.
- [ ] `git -C <export> status --short` is empty (original export untouched).
- [ ] No `@supabase/supabase-js` import left: `git -C <dest> grep -l "@supabase/supabase-js" -- src > sb.txt; echo $? > sb.rc` and `sb.rc` holds `1` (no match).
- [ ] `python gates/G_QUARTETO_SINE_QUA_NON.py --target <dest> > q-freedom.log 2>&1; echo $? > q-freedom.rc` holds `0` on the liberated app, with the exported UI unchanged.
