---
name: aidd-enterprise
description: Injects and audits mission-critical components with JSON Schema validation, SHA-256 integrity and automatic rollback. Use when the user wants to inject a certified skill, rule, mcp, spec, config, hook or agent, or says "enterprise", "/enterprise", "injetar componente", "blindagem SHA-256".
---

# aidd-enterprise

Transactional injection of mission-critical components:
- strict manifest validation against JSON Schema;
- cryptographic integrity check with SHA-256 hashes;
- snapshot and automatic rollback on inconsistency;
- types: `skill`, `rule`, `mcp`, `spec`, `config`, `hook`, `agent`.

## Run

```bash
python ecossistema.py enterprise inject <type> <name>
```

Slash command: `/enterprise <type> <name>`.

Done when: the command exits 0 with no hash divergence reported.

## Negative Guardrails

- NEVER run `enterprise inject` without `--dir <target>` and a prior `--dry-run`: the default `.` injects into the repository you are in (seen in the AIDD-Ops batteries).
- NEVER use `--remover` to delete an injected component without explicit user OK.
- NEVER delete `.ENTERPRISE-SNAPSHOT/` or `.ENTERPRISE-ROLLBACK-JOURNAL.json` by hand; recover with `python componentes/compartilhado/skills/aidd-enterprise/scripts/rollback.py <target>`.
- NEVER fix a SHA-256 divergence by rewriting `CAPABILITIES.json` hashes; find who edited the component, then re-inject it.
- NEVER mistype the subcommand: `tools/aidd-enterprise/scripts/aidd.py` routes unknown words to natural-language injection instead of failing.
- NEVER put real tokens in `--mcp-env`; pass variable names and let the user fill values.

## Failure Modes & Fallback

- **Injection fails mid-way:** the transaction restores snapshots; confirm with `rollback.py <target>` printing "workspace limpo" (exit 0). Exit 1 means still dirty: stop and show the user the listed files.
- **`enterprise verificar-drift --dir <target>` reports a divergent hash:** someone edited an injected file. Ask the user whether to keep the edit (re-inject from it) or restore the certified version.
- **`python gates/G_aidd_enterprise.py --manifest <file> --dir <target>` exits 1:** fix the manifest fields against the schema, then rerun `inject --dry-run`.

## Stopping Checklist

- [ ] `python ecossistema.py enterprise inject <type> <name> --dir <target> --dry-run > dry.log 2>&1; echo $? > dry.rc` holds `0` before the real run.
- [ ] `python ecossistema.py enterprise inject <type> <name> --dir <target> > inj.log 2>&1; echo $? > inj.rc` holds `0`.
- [ ] `python ecossistema.py enterprise verificar-drift --dir <target> > drift.log 2>&1; echo $? > drift.rc` holds `0`.
- [ ] `<target>/.ENTERPRISE-ROLLBACK-JOURNAL.json` does not exist (transaction closed).
