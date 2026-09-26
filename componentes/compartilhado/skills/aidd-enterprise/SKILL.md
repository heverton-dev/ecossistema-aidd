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
